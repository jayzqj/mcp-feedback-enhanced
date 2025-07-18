#!/usr/bin/env python3
"""
Web UI 主要管理类

基于 FastAPI 的 Web 用户界面主要管理类，采用现代化架构设计。
提供完整的回馈收集、图片上传、命令执行等功能。
"""

import asyncio
import concurrent.futures
import os
import threading
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from ..debug import web_debug_log as debug_log
from ..utils.error_handler import ErrorHandler, ErrorType
from ..utils.memory_monitor import get_memory_monitor
from .models import CleanupReason, SessionStatus, WebFeedbackSession
from .routes import setup_routes
from .utils import get_browser_opener
from .utils.compression_config import get_compression_manager
from .utils.port_manager import PortManager


class WebUIManager:
    """Web UI 管理器 - 重构为单一活跃会话模式"""

    def __init__(self, host: str = "127.0.0.1", port: int | None = None):
        # 确定偏好主机：环境变量 > 参数 > 默认值 127.0.0.1
        env_host = os.getenv("MCP_WEB_HOST")
        if env_host:
            self.host = env_host
            debug_log(f"使用环境变量指定的主机: {self.host}")
        else:
            self.host = host
            debug_log(f"未设定 MCP_WEB_HOST 环境变量，使用默认主机 {self.host}")

        # 确定偏好端口：环境变量 > 参数 > 默认值 8765
        preferred_port = 8765

        # 检查环境变量 MCP_WEB_PORT
        env_port = os.getenv("MCP_WEB_PORT")
        if env_port:
            try:
                custom_port = int(env_port)
                if custom_port == 0:
                    # 特殊值 0 表示使用系统自动分配的端口
                    preferred_port = 0
                    debug_log("使用环境变量指定的自动端口分配 (0)")
                elif 1024 <= custom_port <= 65535:
                    preferred_port = custom_port
                    debug_log(f"使用环境变量指定的端口: {preferred_port}")
                else:
                    debug_log(
                        f"MCP_WEB_PORT 值无效 ({custom_port})，必须在 1024-65535 范围内或为 0，使用默认端口 8765"
                    )
            except ValueError:
                debug_log(
                    f"MCP_WEB_PORT 格式错误 ({env_port})，必须为数字，使用默认端口 8765"
                )
        else:
            debug_log(f"未设定 MCP_WEB_PORT 环境变量，使用默认端口 {preferred_port}")

        # 使用增强的端口管理，测试模式下禁用自动清理避免权限问题
        auto_cleanup = os.environ.get("MCP_TEST_MODE", "").lower() != "true"

        if port is not None:
            # 如果明确指定了端口，使用指定的端口
            self.port = port
            # 检查指定端口是否可用
            if not PortManager.is_port_available(self.host, self.port):
                debug_log(f"警告：指定的端口 {self.port} 可能已被占用")
                # 在测试模式下，尝试寻找替代端口
                if os.environ.get("MCP_TEST_MODE", "").lower() == "true":
                    debug_log("测试模式：自动寻找替代端口")
                    original_port = self.port
                    self.port = PortManager.find_free_port_enhanced(
                        preferred_port=self.port, auto_cleanup=False, host=self.host
                    )
                    if self.port != original_port:
                        debug_log(f"自动切换到可用端口: {original_port} → {self.port}")
        elif preferred_port == 0:
            # 如果偏好端口为 0，使用系统自动分配
            import socket

            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind((self.host, 0))
                self.port = s.getsockname()[1]
            debug_log(f"系统自动分配端口: {self.port}")
        else:
            # 使用增强的端口管理
            self.port = PortManager.find_free_port_enhanced(
                preferred_port=preferred_port, auto_cleanup=auto_cleanup, host=self.host
            )
        self.app = FastAPI(title="MCP Feedback Enhanced")

        # 设置压缩和缓存中间件
        self._setup_compression_middleware()

        # 设置内存监控
        self._setup_memory_monitoring()

        # 重构：使用单一活跃会话而非会话字典
        self.current_session: WebFeedbackSession | None = None
        self.sessions: dict[str, WebFeedbackSession] = {}  # 保留用于向后兼容

        # 全局标签页状态管理 - 跨会话保持
        self.global_active_tabs: dict[str, dict] = {}

        # 会话更新通知标记
        self._pending_session_update = False

        # 会话清理统计
        self.cleanup_stats: dict[str, Any] = {
            "total_cleanups": 0,
            "expired_cleanups": 0,
            "memory_pressure_cleanups": 0,
            "manual_cleanups": 0,
            "last_cleanup_time": None,
            "total_cleanup_duration": 0.0,
            "sessions_cleaned": 0,
        }

        self.server_thread: threading.Thread | None = None
        self.server_process = None
        self.desktop_app_instance: Any = None  # 桌面应用实例引用

        # 初始化标记，用于追踪异步初始化状态
        self._initialization_complete = False
        self._initialization_lock = threading.Lock()

        # 同步初始化基本组件
        self._init_basic_components()

        debug_log(f"WebUIManager 基本初始化完成，将在 {self.host}:{self.port} 启动")
        debug_log("回馈模式: web")

    def _init_basic_components(self):
        """同步初始化基本组件"""
        # 基本组件初始化（必须同步）
        # 移除 i18n 管理器，因为翻译已移至前端

        # 设置静态文件和模板（必须同步）
        self._setup_static_files()
        self._setup_templates()

        # 设置路由（必须同步）
        setup_routes(self)

    async def _init_async_components(self):
        """异步初始化组件（并行执行）"""
        with self._initialization_lock:
            if self._initialization_complete:
                return

        debug_log("开始并行初始化组件...")
        start_time = time.time()

        # 创建并行任务
        tasks = []

        # 任务：I18N 预载入（如果需要）
        tasks.append(self._preload_i18n_async())

        # 并行执行所有任务
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # 检查结果
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    debug_log(f"并行初始化任务 {i} 失败: {result}")

        with self._initialization_lock:
            self._initialization_complete = True

        elapsed = time.time() - start_time
        debug_log(f"并行初始化完成，耗时: {elapsed:.2f}秒")

    async def _preload_i18n_async(self):
        """异步预载入 I18N 资源"""

        def preload_i18n():
            try:
                # I18N 在前端处理，这里只记录预载入完成
                debug_log("I18N 资源预载入完成（前端处理）")
                return True
            except Exception as e:
                debug_log(f"I18N 资源预载入失败: {e}")
                return False

        # 在线程池中执行
        loop = asyncio.get_event_loop()
        with concurrent.futures.ThreadPoolExecutor() as executor:
            await loop.run_in_executor(executor, preload_i18n)

    def _setup_compression_middleware(self):
        """设置压缩和缓存中间件"""
        # 获取压缩管理器
        compression_manager = get_compression_manager()
        config = compression_manager.config

        # 添加 Gzip 压缩中间件
        self.app.add_middleware(GZipMiddleware, minimum_size=config.minimum_size)

        # 添加缓存和压缩统计中间件
        @self.app.middleware("http")
        async def compression_and_cache_middleware(request: Request, call_next):
            """压缩和缓存中间件"""
            response = await call_next(request)

            # 添加缓存头
            if not config.should_exclude_path(request.url.path):
                cache_headers = config.get_cache_headers(request.url.path)
                for key, value in cache_headers.items():
                    response.headers[key] = value

            # 更新压缩统计（如果可能）
            try:
                content_length = int(response.headers.get("content-length", 0))
                content_encoding = response.headers.get("content-encoding", "")
                was_compressed = "gzip" in content_encoding

                if content_length > 0:
                    # 估算原始大小（如果已压缩，假设压缩比为 30%）
                    original_size = (
                        content_length
                        if not was_compressed
                        else int(content_length / 0.7)
                    )
                    compression_manager.update_stats(
                        original_size, content_length, was_compressed
                    )
            except (ValueError, TypeError):
                # 忽略统计错误，不影响正常响应
                pass

            return response

        debug_log("压缩和缓存中间件设置完成")

    def _setup_memory_monitoring(self):
        """设置内存监控"""
        try:
            self.memory_monitor = get_memory_monitor()

            # 添加 Web 应用特定的警告回调
            def web_memory_alert(alert):
                debug_log(f"Web UI 内存警告 [{alert.level}]: {alert.message}")

                # 根据警告级别触发不同的清理策略
                if alert.level == "critical":
                    # 危险级别：清理过期会话
                    cleaned = self.cleanup_expired_sessions()
                    debug_log(f"内存危险警告触发，清理了 {cleaned} 个过期会话")
                elif alert.level == "emergency":
                    # 紧急级别：强制清理会话
                    cleaned = self.cleanup_sessions_by_memory_pressure(force=True)
                    debug_log(f"内存紧急警告触发，强制清理了 {cleaned} 个会话")

            self.memory_monitor.add_alert_callback(web_memory_alert)

            # 添加会话清理回调到内存监控
            def session_cleanup_callback(force: bool = False):
                """内存监控触发的会话清理回调"""
                try:
                    if force:
                        # 强制清理：包括内存压力清理
                        cleaned = self.cleanup_sessions_by_memory_pressure(force=True)
                        debug_log(f"内存监控强制清理了 {cleaned} 个会话")
                    else:
                        # 常规清理：只清理过期会话
                        cleaned = self.cleanup_expired_sessions()
                        debug_log(f"内存监控清理了 {cleaned} 个过期会话")
                except Exception as e:
                    error_id = ErrorHandler.log_error_with_context(
                        e,
                        context={"operation": "内存监控会话清理", "force": force},
                        error_type=ErrorType.SYSTEM,
                    )
                    debug_log(f"内存监控会话清理失败 [错误ID: {error_id}]: {e}")

            self.memory_monitor.add_cleanup_callback(session_cleanup_callback)

            # 确保内存监控已启动（ResourceManager 可能已经启动了）
            if not self.memory_monitor.is_monitoring:
                self.memory_monitor.start_monitoring()

            debug_log("Web UI 内存监控设置完成，已集成会话清理回调")

        except Exception as e:
            error_id = ErrorHandler.log_error_with_context(
                e,
                context={"operation": "设置 Web UI 内存监控"},
                error_type=ErrorType.SYSTEM,
            )
            debug_log(f"设置 Web UI 内存监控失败 [错误ID: {error_id}]: {e}")

    def _setup_static_files(self):
        """设置静态文件服务"""
        # Web UI 静态文件
        web_static_path = Path(__file__).parent / "static"
        if web_static_path.exists():
            self.app.mount(
                "/static", StaticFiles(directory=str(web_static_path)), name="static"
            )
        else:
            raise RuntimeError(f"Static files directory not found: {web_static_path}")

    def _setup_templates(self):
        """设置模板引擎"""
        # Web UI 模板
        web_templates_path = Path(__file__).parent / "templates"
        if web_templates_path.exists():
            self.templates = Jinja2Templates(directory=str(web_templates_path))
        else:
            raise RuntimeError(f"Templates directory not found: {web_templates_path}")

    def create_session(self, project_directory: str, summary: str) -> str:
        """创建新的回馈会话 - 重构为单一活跃会话模式，保留标签页状态"""
        # 保存旧会话的引用和 WebSocket 连接
        old_session = self.current_session
        old_websocket = None
        if old_session and old_session.websocket:
            old_websocket = old_session.websocket
            debug_log("保存旧会话的 WebSocket 连接以发送更新通知")

        # 创建新会话
        session_id = str(uuid.uuid4())
        session = WebFeedbackSession(session_id, project_directory, summary)

        # 如果有旧会话，处理状态转换和清理
        if old_session:
            debug_log(
                f"处理旧会话 {old_session.session_id} 的状态转换，当前状态: {old_session.status.value}"
            )

            # 保存标签页状态到全局
            if hasattr(old_session, "active_tabs"):
                self._merge_tabs_to_global(old_session.active_tabs)

            # 如果旧会话是已提交状态，进入下一步（已完成）
            if old_session.status == SessionStatus.FEEDBACK_SUBMITTED:
                debug_log(
                    f"旧会话 {old_session.session_id} 进入下一步：已提交 → 已完成"
                )
                success = old_session.next_step("反馈已处理，会话完成")
                if success:
                    debug_log(f"✅ 旧会话 {old_session.session_id} 成功进入已完成状态")
                else:
                    debug_log(f"❌ 旧会话 {old_session.session_id} 无法进入下一步")
            else:
                debug_log(
                    f"旧会话 {old_session.session_id} 状态为 {old_session.status.value}，无需转换"
                )

            # 确保旧会话仍在字典中（用于API获取）
            if old_session.session_id in self.sessions:
                debug_log(f"旧会话 {old_session.session_id} 仍在会话字典中")
            else:
                debug_log(f"⚠️ 旧会话 {old_session.session_id} 不在会话字典中，重新添加")
                self.sessions[old_session.session_id] = old_session

            # 同步清理会话资源（但保留 WebSocket 连接）
            old_session._cleanup_sync()

        # 将全局标签页状态继承到新会话
        session.active_tabs = self.global_active_tabs.copy()

        # 设置为当前活跃会话
        self.current_session = session
        # 同时保存到字典中以保持向后兼容
        self.sessions[session_id] = session

        debug_log(f"创建新的活跃会话: {session_id}")
        debug_log(f"继承 {len(session.active_tabs)} 个活跃标签页")

        # 处理WebSocket连接转移
        if old_websocket:
            # 直接转移连接到新会话，消息发送由 smart_open_browser 统一处理
            session.websocket = old_websocket
            debug_log("已将旧 WebSocket 连接转移到新会话")
        else:
            # 没有旧连接，标记需要发送会话更新通知（当新 WebSocket 连接建立时）
            self._pending_session_update = True
            debug_log("没有旧 WebSocket 连接，设置待更新标记")

        return session_id

    def get_session(self, session_id: str) -> WebFeedbackSession | None:
        """获取回馈会话 - 保持向后兼容"""
        return self.sessions.get(session_id)

    def get_current_session(self) -> WebFeedbackSession | None:
        """获取当前活跃会话"""
        return self.current_session

    def remove_session(self, session_id: str):
        """移除回馈会话"""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            session.cleanup()
            del self.sessions[session_id]

            # 如果移除的是当前活跃会话，清空当前会话
            if self.current_session and self.current_session.session_id == session_id:
                self.current_session = None
                debug_log("清空当前活跃会话")

            debug_log(f"移除回馈会话: {session_id}")

    def clear_current_session(self):
        """清空当前活跃会话"""
        if self.current_session:
            session_id = self.current_session.session_id
            self.current_session.cleanup()
            self.current_session = None

            # 同时从字典中移除
            if session_id in self.sessions:
                del self.sessions[session_id]

            debug_log("已清空当前活跃会话")

    def _merge_tabs_to_global(self, session_tabs: dict):
        """将会话的标签页状态合并到全局状态"""
        current_time = time.time()
        expired_threshold = 60  # 60秒过期阈值

        # 清理过期的全局标签页
        self.global_active_tabs = {
            tab_id: tab_info
            for tab_id, tab_info in self.global_active_tabs.items()
            if current_time - tab_info.get("last_seen", 0) <= expired_threshold
        }

        # 合并会话标签页到全局
        for tab_id, tab_info in session_tabs.items():
            if current_time - tab_info.get("last_seen", 0) <= expired_threshold:
                self.global_active_tabs[tab_id] = tab_info

        debug_log(f"合并标签页状态，全局活跃标签页数量: {len(self.global_active_tabs)}")

    def get_global_active_tabs_count(self) -> int:
        """获取全局活跃标签页数量"""
        current_time = time.time()
        expired_threshold = 60

        # 清理过期标签页并返回数量
        valid_tabs = {
            tab_id: tab_info
            for tab_id, tab_info in self.global_active_tabs.items()
            if current_time - tab_info.get("last_seen", 0) <= expired_threshold
        }

        self.global_active_tabs = valid_tabs
        return len(valid_tabs)

    async def broadcast_to_active_tabs(self, message: dict):
        """向所有活跃标签页广播消息"""
        if not self.current_session or not self.current_session.websocket:
            debug_log("没有活跃的 WebSocket 连接，无法广播消息")
            return

        try:
            await self.current_session.websocket.send_json(message)
            debug_log(f"已广播消息到活跃标签页: {message.get('type', 'unknown')}")
        except Exception as e:
            debug_log(f"广播消息失败: {e}")

    def start_server(self):
        """启动 Web 服务器（优化版本，支持并行初始化）"""

        def run_server_with_retry():
            max_retries = 5
            retry_count = 0
            original_port = self.port

            while retry_count < max_retries:
                try:
                    # 在尝试启动前先检查端口是否可用
                    if not PortManager.is_port_available(self.host, self.port):
                        debug_log(f"端口 {self.port} 已被占用，自动寻找替代端口")

                        # 查找占用端口的进程信息
                        process_info = PortManager.find_process_using_port(self.port)
                        if process_info:
                            debug_log(
                                f"端口 {self.port} 被进程 {process_info['name']} "
                                f"(PID: {process_info['pid']}) 占用"
                            )

                        # 自动寻找新端口
                        try:
                            new_port = PortManager.find_free_port_enhanced(
                                preferred_port=self.port,
                                auto_cleanup=False,  # 不自动清理其他进程
                                host=self.host,
                            )
                            debug_log(f"自动切换端口: {self.port} → {new_port}")
                            self.port = new_port
                        except RuntimeError as port_error:
                            error_id = ErrorHandler.log_error_with_context(
                                port_error,
                                context={
                                    "operation": "端口查找",
                                    "original_port": original_port,
                                    "current_port": self.port,
                                },
                                error_type=ErrorType.NETWORK,
                            )
                            debug_log(
                                f"无法找到可用端口 [错误ID: {error_id}]: {port_error}"
                            )
                            raise RuntimeError(
                                f"无法找到可用端口，原始端口 {original_port} 被占用"
                            ) from port_error

                    debug_log(
                        f"尝试启动服务器在 {self.host}:{self.port} (尝试 {retry_count + 1}/{max_retries})"
                    )

                    config = uvicorn.Config(
                        app=self.app,
                        host=self.host,
                        port=self.port,
                        log_level="warning",
                        access_log=False,
                    )

                    server_instance = uvicorn.Server(config)

                    # 创建事件循环并启动服务器
                    async def serve_with_async_init(server=server_instance):
                        # 在服务器启动的同时进行异步初始化
                        server_task = asyncio.create_task(server.serve())
                        init_task = asyncio.create_task(self._init_async_components())

                        # 等待两个任务完成
                        await asyncio.gather(
                            server_task, init_task, return_exceptions=True
                        )

                    asyncio.run(serve_with_async_init())

                    # 成功启动，显示最终使用的端口
                    if self.port != original_port:
                        debug_log(
                            f"✅ 服务器成功启动在替代端口 {self.port} (原端口 {original_port} 被占用)"
                        )

                    break

                except OSError as e:
                    if e.errno in {
                        10048,
                        98,
                    }:  # Windows: 10048, Linux: 98 (地址已在使用中)
                        retry_count += 1
                        if retry_count < max_retries:
                            debug_log(
                                f"端口 {self.port} 启动失败 (OSError)，尝试下一个端口"
                            )
                            # 尝试下一个端口
                            self.port = self.port + 1
                        else:
                            debug_log("已达到最大重试次数，无法启动服务器")
                            break
                    else:
                        # 使用统一错误处理
                        error_id = ErrorHandler.log_error_with_context(
                            e,
                            context={
                                "operation": "服务器启动",
                                "host": self.host,
                                "port": self.port,
                            },
                            error_type=ErrorType.NETWORK,
                        )
                        debug_log(f"服务器启动错误 [错误ID: {error_id}]: {e}")
                        break
                except Exception as e:
                    # 使用统一错误处理
                    error_id = ErrorHandler.log_error_with_context(
                        e,
                        context={
                            "operation": "服务器运行",
                            "host": self.host,
                            "port": self.port,
                        },
                        error_type=ErrorType.SYSTEM,
                    )
                    debug_log(f"服务器运行错误 [错误ID: {error_id}]: {e}")
                    break

        # 在新线程中启动服务器
        self.server_thread = threading.Thread(target=run_server_with_retry, daemon=True)
        self.server_thread.start()

        # 等待服务器启动
        time.sleep(2)

    def open_browser(self, url: str):
        """开启浏览器"""
        try:
            browser_opener = get_browser_opener()
            browser_opener(url)
            debug_log(f"已开启浏览器：{url}")
        except Exception as e:
            debug_log(f"无法开启浏览器: {e}")

    async def smart_open_browser(self, url: str) -> bool:
        """智能开启浏览器 - 检测是否已有活跃标签页

        Returns:
            bool: True 表示检测到活跃标签页或桌面模式，False 表示开启了新窗口
        """

        try:
            # 检查是否为桌面模式
            if os.environ.get("MCP_DESKTOP_MODE", "").lower() == "true":
                debug_log("检测到桌面模式，跳过浏览器开启")
                return True

            # 检查是否有活跃标签页
            has_active_tabs = await self._check_active_tabs()

            if has_active_tabs:
                debug_log("检测到活跃标签页，发送刷新通知")
                debug_log(f"向现有标签页发送刷新通知：{url}")

                # 向现有标签页发送刷新通知
                refresh_success = await self.notify_existing_tab_to_refresh()

                debug_log(f"刷新通知发送结果: {refresh_success}")
                debug_log("检测到活跃标签页，不开启新浏览器窗口")
                return True

            # 没有活跃标签页，开启新浏览器窗口
            debug_log("没有检测到活跃标签页，开启新浏览器窗口")
            self.open_browser(url)
            return False

        except Exception as e:
            debug_log(f"智能浏览器开启失败，回退到普通开启：{e}")
            self.open_browser(url)
            return False

    async def launch_desktop_app(self, url: str) -> bool:
        """
        启动桌面应用程序

        Args:
            url: Web 服务 URL

        Returns:
            bool: True 表示成功启动桌面应用程序
        """
        try:
            # 尝试导入桌面应用程序模块
            def import_desktop_app():
                # 首先尝试从发布包位置导入
                try:
                    from mcp_feedback_enhanced.desktop_app import (
                        launch_desktop_app as desktop_func,
                    )

                    debug_log("使用发布包中的桌面应用程序模块")
                    return desktop_func
                except ImportError:
                    debug_log("发布包中未找到桌面应用程序模块，尝试开发环境...")

                # 回退到开发环境路径
                import sys

                project_root = os.path.dirname(
                    os.path.dirname(os.path.dirname(__file__))
                )
                desktop_module_path = os.path.join(project_root, "src-tauri", "python")
                if desktop_module_path not in sys.path:
                    sys.path.insert(0, desktop_module_path)
                try:
                    from mcp_feedback_enhanced_desktop import (  # type: ignore
                        launch_desktop_app as dev_func,
                    )

                    debug_log("使用开发环境桌面应用程序模块")
                    return dev_func
                except ImportError:
                    debug_log("无法从开发环境路径导入桌面应用程序模块")
                    debug_log("这可能是 PyPI 安装的版本，桌面应用功能不可用")
                    raise

            launch_desktop_app_func = import_desktop_app()

            # 启动桌面应用程序
            desktop_app = await launch_desktop_app_func()
            # 保存桌面应用实例引用，以便后续控制
            self.desktop_app_instance = desktop_app
            debug_log("桌面应用程序启动成功")
            return True

        except ImportError as e:
            debug_log(f"无法导入桌面应用程序模块: {e}")
            debug_log("回退到浏览器模式...")
            self.open_browser(url)
            return False
        except Exception as e:
            debug_log(f"桌面应用程序启动失败: {e}")
            debug_log("回退到浏览器模式...")
            self.open_browser(url)
            return False

    def close_desktop_app(self):
        """关闭桌面应用程序"""
        if self.desktop_app_instance:
            try:
                debug_log("正在关闭桌面应用程序...")
                self.desktop_app_instance.stop()
                self.desktop_app_instance = None
                debug_log("桌面应用程序已关闭")
            except Exception as e:
                debug_log(f"关闭桌面应用程序失败: {e}")
        else:
            debug_log("没有活跃的桌面应用程序实例")

    async def _safe_close_websocket(self, websocket):
        """安全关闭 WebSocket 连接，避免事件循环冲突 - 仅在连接已转移后调用"""
        if not websocket:
            return

        # 注意：此方法现在主要用于清理，因为连接已经转移到新会话
        # 只有在确认连接没有被新会话使用时才关闭
        try:
            # 检查连接状态
            if (
                hasattr(websocket, "client_state")
                and websocket.client_state.DISCONNECTED
            ):
                debug_log("WebSocket 已断开，跳过关闭操作")
                return

            # 由于连接已转移到新会话，这里不再主动关闭
            # 让新会话管理这个连接的生命周期
            debug_log("WebSocket 连接已转移到新会话，跳过关闭操作")

        except Exception as e:
            debug_log(f"检查 WebSocket 连接状态时发生错误: {e}")

    async def notify_existing_tab_to_refresh(self) -> bool:
        """通知现有标签页刷新显示新会话内容

        Returns:
            bool: True 表示成功发送，False 表示失败
        """
        try:
            if not self.current_session or not self.current_session.websocket:
                debug_log("没有活跃的WebSocket连接，无法发送刷新通知")
                return False

            # 构建刷新通知消息
            refresh_message = {
                "type": "session_updated",
                "action": "new_session_created",
                "messageCode": "session.created",
                "session_info": {
                    "session_id": self.current_session.session_id,
                    "project_directory": self.current_session.project_directory,
                    "summary": self.current_session.summary,
                    "status": self.current_session.status.value,
                },
            }

            # 发送刷新通知
            await self.current_session.websocket.send_json(refresh_message)
            debug_log(f"已向现有标签页发送刷新通知: {self.current_session.session_id}")

            # 简单等待一下让消息发送完成
            await asyncio.sleep(0.2)
            debug_log("刷新通知发送完成")
            return True

        except Exception as e:
            debug_log(f"发送刷新通知失败: {e}")
            return False

    async def _check_active_tabs(self) -> bool:
        """检查是否有活跃标签页 - 使用分层检测机制"""
        try:
            # 快速检测层：检查 WebSocket 对象是否存在
            if not self.current_session or not self.current_session.websocket:
                debug_log("快速检测：没有当前会话或 WebSocket 连接")
                return False

            # 检查心跳（如果有心跳记录）
            last_heartbeat = getattr(self.current_session, "last_heartbeat", None)
            if last_heartbeat:
                heartbeat_age = time.time() - last_heartbeat
                if heartbeat_age > 10:  # 超过 10 秒没有心跳
                    debug_log(f"快速检测：心跳超时 ({heartbeat_age:.1f}秒)")
                    # 可能连接已死，需要进一步检测
                else:
                    debug_log(f"快速检测：心跳正常 ({heartbeat_age:.1f}秒前)")
                    return True  # 心跳正常，认为连接活跃

            # 准确检测层：实际测试连接是否活着
            try:
                # 检查 WebSocket 连接状态
                websocket = self.current_session.websocket

                # 检查连接是否已关闭
                if hasattr(websocket, "client_state"):
                    try:
                        # 尝试从 starlette 导入（FastAPI 基于 Starlette）
                        import starlette.websockets  # type: ignore[import-not-found]

                        if hasattr(starlette.websockets, "WebSocketState"):
                            WebSocketState = starlette.websockets.WebSocketState
                            if websocket.client_state != WebSocketState.CONNECTED:
                                debug_log(
                                    f"准确检测：WebSocket 状态不是 CONNECTED，而是 {websocket.client_state}"
                                )
                                # 清理死连接
                                self.current_session.websocket = None
                                return False
                    except ImportError:
                        # 如果导入失败，使用替代方法
                        debug_log("无法导入 WebSocketState，使用替代方法检测连接")
                        # 跳过状态检查，直接测试连接

                # 如果连接看起来是活的，尝试发送 ping（非阻塞）
                # 注意：FastAPI WebSocket 没有内建的 ping 方法，这里使用自定义消息
                await websocket.send_json({"type": "ping", "timestamp": time.time()})
                debug_log("准确检测：成功发送 ping 消息，连接是活跃的")
                return True

            except Exception as e:
                debug_log(f"准确检测：连接测试失败 - {e}")
                # 连接已死，清理它
                if self.current_session:
                    self.current_session.websocket = None
                return False

        except Exception as e:
            debug_log(f"检查活跃连接时发生错误：{e}")
            return False

    def get_server_url(self) -> str:
        """获取服务器 URL"""
        return f"http://{self.host}:{self.port}"

    def cleanup_expired_sessions(self) -> int:
        """清理过期会话"""
        cleanup_start_time = time.time()
        expired_sessions = []

        # 扫描过期会话
        for session_id, session in self.sessions.items():
            if session.is_expired():
                expired_sessions.append(session_id)

        # 批量清理过期会话
        cleaned_count = 0
        for session_id in expired_sessions:
            try:
                if session_id in self.sessions:
                    session = self.sessions[session_id]
                    # 使用增强清理方法
                    session._cleanup_sync_enhanced(CleanupReason.EXPIRED)
                    del self.sessions[session_id]
                    cleaned_count += 1

                    # 如果清理的是当前活跃会话，清空当前会话
                    if (
                        self.current_session
                        and self.current_session.session_id == session_id
                    ):
                        self.current_session = None
                        debug_log("清空过期的当前活跃会话")

            except Exception as e:
                error_id = ErrorHandler.log_error_with_context(
                    e,
                    context={"session_id": session_id, "operation": "清理过期会话"},
                    error_type=ErrorType.SYSTEM,
                )
                debug_log(f"清理过期会话 {session_id} 失败 [错误ID: {error_id}]: {e}")

        # 更新统计
        cleanup_duration = time.time() - cleanup_start_time
        self.cleanup_stats.update(
            {
                "total_cleanups": self.cleanup_stats["total_cleanups"] + 1,
                "expired_cleanups": self.cleanup_stats["expired_cleanups"] + 1,
                "last_cleanup_time": datetime.now().isoformat(),
                "total_cleanup_duration": self.cleanup_stats["total_cleanup_duration"]
                + cleanup_duration,
                "sessions_cleaned": self.cleanup_stats["sessions_cleaned"]
                + cleaned_count,
            }
        )

        if cleaned_count > 0:
            debug_log(
                f"清理了 {cleaned_count} 个过期会话，耗时: {cleanup_duration:.2f}秒"
            )

        return cleaned_count

    def cleanup_sessions_by_memory_pressure(self, force: bool = False) -> int:
        """根据内存压力清理会话"""
        cleanup_start_time = time.time()
        sessions_to_clean = []

        # 根据优先级选择要清理的会话
        # 优先级：已完成 > 已提交反馈 > 错误状态 > 空闲时间最长
        for session_id, session in self.sessions.items():
            # 跳过当前活跃会话（除非强制清理）
            if (
                not force
                and self.current_session
                and session.session_id == self.current_session.session_id
            ):
                continue

            # 优先清理已完成或错误状态的会话
            if session.status in [
                SessionStatus.COMPLETED,
                SessionStatus.ERROR,
                SessionStatus.TIMEOUT,
            ]:
                sessions_to_clean.append((session_id, session, 1))  # 高优先级
            elif session.status == SessionStatus.FEEDBACK_SUBMITTED:
                # 已提交反馈但空闲时间较长的会话
                if session.get_idle_time() > 300:  # 5分钟空闲
                    sessions_to_clean.append((session_id, session, 2))  # 中优先级
            elif session.get_idle_time() > 600:  # 10分钟空闲
                sessions_to_clean.append((session_id, session, 3))  # 低优先级

        # 按优先级排序
        sessions_to_clean.sort(key=lambda x: x[2])

        # 清理会话（限制数量避免过度清理）
        max_cleanup = min(
            len(sessions_to_clean), 5 if not force else len(sessions_to_clean)
        )
        cleaned_count = 0

        for i in range(max_cleanup):
            session_id, session, priority = sessions_to_clean[i]
            try:
                # 使用增强清理方法
                session._cleanup_sync_enhanced(CleanupReason.MEMORY_PRESSURE)
                del self.sessions[session_id]
                cleaned_count += 1

                # 如果清理的是当前活跃会话，清空当前会话
                if (
                    self.current_session
                    and self.current_session.session_id == session_id
                ):
                    self.current_session = None
                    debug_log("因内存压力清空当前活跃会话")

            except Exception as e:
                error_id = ErrorHandler.log_error_with_context(
                    e,
                    context={"session_id": session_id, "operation": "内存压力清理"},
                    error_type=ErrorType.SYSTEM,
                )
                debug_log(
                    f"内存压力清理会话 {session_id} 失败 [错误ID: {error_id}]: {e}"
                )

        # 更新统计
        cleanup_duration = time.time() - cleanup_start_time
        self.cleanup_stats.update(
            {
                "total_cleanups": self.cleanup_stats["total_cleanups"] + 1,
                "memory_pressure_cleanups": self.cleanup_stats[
                    "memory_pressure_cleanups"
                ]
                + 1,
                "last_cleanup_time": datetime.now().isoformat(),
                "total_cleanup_duration": self.cleanup_stats["total_cleanup_duration"]
                + cleanup_duration,
                "sessions_cleaned": self.cleanup_stats["sessions_cleaned"]
                + cleaned_count,
            }
        )

        if cleaned_count > 0:
            debug_log(
                f"因内存压力清理了 {cleaned_count} 个会话，耗时: {cleanup_duration:.2f}秒"
            )

        return cleaned_count

    def get_session_cleanup_stats(self) -> dict:
        """获取会话清理统计"""
        stats = self.cleanup_stats.copy()
        stats.update(
            {
                "active_sessions": len(self.sessions),
                "current_session_id": self.current_session.session_id
                if self.current_session
                else None,
                "expired_sessions": sum(
                    1 for s in self.sessions.values() if s.is_expired()
                ),
                "idle_sessions": sum(
                    1 for s in self.sessions.values() if s.get_idle_time() > 300
                ),
                "memory_usage_mb": 0,  # 将在下面计算
            }
        )

        # 计算内存使用（如果可能）
        try:
            import psutil

            process = psutil.Process()
            stats["memory_usage_mb"] = round(
                process.memory_info().rss / (1024 * 1024), 2
            )
        except:
            pass

        return stats

    def _scan_expired_sessions(self) -> list[str]:
        """扫描过期会话ID列表"""
        expired_sessions = []
        for session_id, session in self.sessions.items():
            if session.is_expired():
                expired_sessions.append(session_id)
        return expired_sessions

    def stop(self):
        """停止 Web UI 服务"""
        # 清理所有会话
        cleanup_start_time = time.time()
        session_count = len(self.sessions)

        for session in list(self.sessions.values()):
            try:
                session._cleanup_sync_enhanced(CleanupReason.SHUTDOWN)
            except Exception as e:
                debug_log(f"停止服务时清理会话失败: {e}")

        self.sessions.clear()
        self.current_session = None

        # 更新统计
        cleanup_duration = time.time() - cleanup_start_time
        self.cleanup_stats.update(
            {
                "total_cleanups": self.cleanup_stats["total_cleanups"] + 1,
                "manual_cleanups": self.cleanup_stats["manual_cleanups"] + 1,
                "last_cleanup_time": datetime.now().isoformat(),
                "total_cleanup_duration": self.cleanup_stats["total_cleanup_duration"]
                + cleanup_duration,
                "sessions_cleaned": self.cleanup_stats["sessions_cleaned"]
                + session_count,
            }
        )

        debug_log(
            f"停止服务时清理了 {session_count} 个会话，耗时: {cleanup_duration:.2f}秒"
        )

        # 停止服务器（注意：uvicorn 的 graceful shutdown 需要额外处理）
        if self.server_thread is not None and self.server_thread.is_alive():
            debug_log("正在停止 Web UI 服务")


# 全局实例
_web_ui_manager: WebUIManager | None = None


def get_web_ui_manager() -> WebUIManager:
    """获取 Web UI 管理器实例"""
    global _web_ui_manager
    if _web_ui_manager is None:
        _web_ui_manager = WebUIManager()
    return _web_ui_manager


async def launch_web_feedback_ui(
    project_directory: str, summary: str, timeout: int = 600
) -> dict:
    """
    启动 Web 回馈界面并等待用户回馈 - 重构为使用根路径

    Args:
        project_directory: 项目目录路径
        summary: AI 工作摘要
        timeout: 超时时间（秒）

    Returns:
        dict: 回馈结果，包含 logs、interactive_feedback 和 images
    """
    manager = get_web_ui_manager()

    # 创建新会话（每次AI调用都应该创建新会话）
    manager.create_session(project_directory, summary)
    session = manager.get_current_session()

    if not session:
        raise RuntimeError("无法创建回馈会话")

    # 启动服务器（如果尚未启动）
    if manager.server_thread is None or not manager.server_thread.is_alive():
        manager.start_server()

    # 检查是否为桌面模式
    desktop_mode = os.environ.get("MCP_DESKTOP_MODE", "").lower() == "true"

    # 使用根路径 URL
    feedback_url = manager.get_server_url()  # 直接使用根路径

    if desktop_mode:
        # 桌面模式：启动桌面应用程序
        debug_log("检测到桌面模式，启动桌面应用程序...")
        has_active_tabs = await manager.launch_desktop_app(feedback_url)
    else:
        # Web 模式：智能开启浏览器
        has_active_tabs = await manager.smart_open_browser(feedback_url)

    debug_log(f"[DEBUG] 服务器地址: {feedback_url}")

    # 如果检测到活跃标签页，消息已在 smart_open_browser 中发送，无需额外处理
    if has_active_tabs:
        debug_log("检测到活跃标签页，会话更新通知已发送")

    try:
        # 等待用户回馈，传递 timeout 参数
        result = await session.wait_for_feedback(timeout)
        debug_log("收到用户回馈")
        return result
    except TimeoutError:
        debug_log("会话超时")
        # 资源已在 wait_for_feedback 中清理，这里只需要记录和重新抛出
        raise
    except Exception as e:
        debug_log(f"会话发生错误: {e}")
        raise
    finally:
        # 注意：不再自动清理会话和停止服务器，保持持久性
        # 会话将保持活跃状态，等待下次 MCP 调用
        debug_log("会话保持活跃状态，等待下次 MCP 调用")


def stop_web_ui():
    """停止 Web UI 服务"""
    global _web_ui_manager
    if _web_ui_manager:
        _web_ui_manager.stop()
        _web_ui_manager = None
        debug_log("Web UI 服务已停止")


# 测试用主函数
if __name__ == "__main__":

    async def main():
        try:
            project_dir = os.getcwd()
            summary = """# Markdown 功能测试

## 🎯 任务完成摘要

我已成功为 **mcp-feedback-enhanced** 项目实现了 Markdown 语法显示功能！

### ✅ 完成的功能

1. **标题支持** - 支持 H1 到 H6 标题
2. **文字格式化**
   - **粗体文字** 使用双星号
   - *斜体文字* 使用单星号
   - `行内程序代码` 使用反引号
3. **程序代码区块**
4. **列表功能**
   - 无序列表项目
   - 有序列表项目

### 📋 技术实现

```javascript
// 使用 marked.js 进行 Markdown 解析
const renderedContent = this.renderMarkdownSafely(summary);
element.innerHTML = renderedContent;
```

### 🔗 相关链接

- [marked.js 官方文档](https://marked.js.org/)
- [DOMPurify 安全清理](https://github.com/cure53/DOMPurify)

> **注意**: 此功能包含 XSS 防护，使用 DOMPurify 进行 HTML 清理。

---

**测试状态**: ✅ 功能正常运作"""

            from ..debug import debug_log

            debug_log("启动 Web UI 测试...")
            debug_log(f"项目目录: {project_dir}")
            debug_log("等待用户回馈...")

            result = await launch_web_feedback_ui(project_dir, summary)

            debug_log("收到回馈结果:")
            debug_log(f"命令日志: {result.get('logs', '')}")
            debug_log(f"交互回馈: {result.get('interactive_feedback', '')}")
            debug_log(f"图片数量: {len(result.get('images', []))}")

        except KeyboardInterrupt:
            debug_log("\n用户取消操作")
        except Exception as e:
            debug_log(f"错误: {e}")
        finally:
            stop_web_ui()

    asyncio.run(main())
