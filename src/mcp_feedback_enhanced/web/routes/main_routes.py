#!/usr/bin/env python3
"""
主要路由处理
============

设置 Web UI 的主要路由和处理逻辑。
"""

import json
import time
from pathlib import Path
from typing import TYPE_CHECKING

from fastapi import Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse

from ... import __version__
from ...debug import web_debug_log as debug_log
from ..constants import get_message_code as get_msg_code


if TYPE_CHECKING:
    from ..main import WebUIManager


def load_user_layout_settings() -> str:
    """加载用户的布局模式设置"""
    try:
        # 使用统一的设置文件路径
        config_dir = Path.home() / ".config" / "mcp-feedback-enhanced"
        settings_file = config_dir / "ui_settings.json"

        if settings_file.exists():
            with open(settings_file, encoding="utf-8") as f:
                settings = json.load(f)
                layout_mode = settings.get("layoutMode", "combined-vertical")
                debug_log(f"从设置文件加载布局模式: {layout_mode}")
                # 修复 no-any-return 错误 - 确保返回 str 类型
                return str(layout_mode)
        else:
            debug_log("设置文件不存在，使用默认布局模式: combined-vertical")
            return "combined-vertical"
    except Exception as e:
        debug_log(
            f"加载布局设置失败: {e}，使用默认布局模式: combined-vertical"
        )
        return "combined-vertical"


# 使用统一的消息代码系统
# 从 ..constants 导入的 get_msg_code 函数会处理所有消息代码
# 旧的 key 会自动映射到新的常量


def setup_routes(manager: "WebUIManager"):
    """设置路由"""

    @manager.app.get("/", response_class=HTMLResponse)
    async def index(request: Request):
        """统一回馈页面 - 重构后的主页面"""
        # 获取当前活跃会话
        current_session = manager.get_current_session()

        if not current_session:
            # 没有活跃会话时显示等待页面
            return manager.templates.TemplateResponse(
                "index.html",
                {
                    "request": request,
                    "title": "MCP Feedback Enhanced",
                    "has_session": False,
                    "version": __version__,
                },
            )

        # 有活跃会话时显示回馈页面
        # 加载用户的布局模式设置
        layout_mode = load_user_layout_settings()

        return manager.templates.TemplateResponse(
            "feedback.html",
            {
                "request": request,
                "project_directory": current_session.project_directory,
                "summary": current_session.summary,
                "title": "Interactive Feedback - 回馈收集",
                "version": __version__,
                "has_session": True,
                "layout_mode": layout_mode,
            },
        )

    @manager.app.get("/api/translations")
    async def get_translations():
        """获取翻译数据 - 从 Web 专用翻译文件加载"""
        translations = {}

        # 获取 Web 翻译文件目录
        web_locales_dir = Path(__file__).parent.parent / "locales"
        supported_languages = ["zh-CN"]

        for lang_code in supported_languages:
            lang_dir = web_locales_dir / lang_code
            translation_file = lang_dir / "translation.json"

            try:
                if translation_file.exists():
                    with open(translation_file, encoding="utf-8") as f:
                        lang_data = json.load(f)
                        translations[lang_code] = lang_data
                        debug_log(f"成功加载 Web 翻译: {lang_code}")
                else:
                    debug_log(f"Web 翻译文件不存在: {translation_file}")
                    translations[lang_code] = {}
            except Exception as e:
                debug_log(f"加载 Web 翻译文件失败 {lang_code}: {e}")
                translations[lang_code] = {}

        debug_log(f"Web 翻译 API 返回 {len(translations)} 种语言的数据")
        return JSONResponse(content=translations)

    @manager.app.get("/api/session-status")
    async def get_session_status(request: Request):
        """获取当前会话状态"""
        current_session = manager.get_current_session()

        # 从请求头获取客户端语言
        lang = (
            request.headers.get("Accept-Language", "zh-TW")
            .split(",")[0]
            .split("-")[0]
        )
        if lang == "zh":
            lang = "zh-TW"

        if not current_session:
            return JSONResponse(
                content={
                    "has_session": False,
                    "status": "no_session",
                    "messageCode": get_msg_code("no_active_session"),
                }
            )

        return JSONResponse(
            content={
                "has_session": True,
                "status": "active",
                "session_info": {
                    "project_directory": current_session.project_directory,
                    "summary": current_session.summary,
                    "feedback_completed": current_session.feedback_completed.is_set(),
                },
            }
        )

    @manager.app.get("/api/current-session")
    async def get_current_session(request: Request):
        """获取当前会话详细信息"""
        current_session = manager.get_current_session()

        # 从查询参数获取语言，如果没有则从会话获取，最后使用默认值

        if not current_session:
            return JSONResponse(
                status_code=404,
                content={
                    "error": "No active session",
                    "messageCode": get_msg_code("no_active_session"),
                },
            )

        return JSONResponse(
            content={
                "session_id": current_session.session_id,
                "project_directory": current_session.project_directory,
                "summary": current_session.summary,
                "feedback_completed": current_session.feedback_completed.is_set(),
                "command_logs": current_session.command_logs,
                "images_count": len(current_session.images),
            }
        )

    @manager.app.get("/api/all-sessions")
    async def get_all_sessions(request: Request):
        """获取所有会话的实时状态"""

        try:
            sessions_data = []

            # 获取所有会话的实时状态
            for session_id, session in manager.sessions.items():
                session_info = {
                    "session_id": session.session_id,
                    "project_directory": session.project_directory,
                    "summary": session.summary,
                    "status": session.status.value,
                    "status_message": session.status_message,
                    "created_at": int(session.created_at * 1000),  # 转换为毫秒
                    "last_activity": int(session.last_activity * 1000),
                    "feedback_completed": session.feedback_completed.is_set(),
                    "has_websocket": session.websocket is not None,
                    "is_current": session == manager.current_session,
                    "user_messages": session.user_messages,  # 包含用户消息记录
                }
                sessions_data.append(session_info)

            # 按创建时间排序（最新的在前）
            sessions_data.sort(
                key=lambda x: x["created_at"], reverse=True
            )

            debug_log(f"返回 {len(sessions_data)} 个会话的实时状态")
            return JSONResponse(content={"sessions": sessions_data})

        except Exception as e:
            debug_log(f"获取所有会话状态失败: {e}")
            return JSONResponse(
                status_code=500,
                content={
                    "error": f"Failed to get sessions: {e!s}",
                    "messageCode": get_msg_code("get_sessions_failed"),
                },
            )

    @manager.app.post("/api/add-user-message")
    async def add_user_message(request: Request):
        """添加用户消息到当前会话"""

        try:
            data = await request.json()
            current_session = manager.get_current_session()

            if not current_session:
                return JSONResponse(
                    status_code=404,
                    content={
                        "error": "No active session",
                        "messageCode": get_msg_code("no_active_session"),
                    },
                )

            # 添加用户消息到会话
            current_session.add_user_message(data)

            debug_log(f"用户消息已添加到会话 {current_session.session_id}")
            return JSONResponse(
                content={
                    "status": "success",
                    "messageCode": get_msg_code("user_message_recorded"),
                }
            )

        except Exception as e:
            debug_log(f"添加用户消息失败: {e}")
            return JSONResponse(
                status_code=500,
                content={
                    "error": f"Failed to add user message: {e!s}",
                    "messageCode": get_msg_code("add_user_message_failed"),
                },
            )

    @manager.app.websocket("/ws")
    async def websocket_endpoint(websocket: WebSocket, lang: str = "zh-TW"):
        """WebSocket 端点 - 重构后移除 session_id 依赖"""
        # 获取当前活跃会话
        session = manager.get_current_session()
        if not session:
            await websocket.close(code=4004, reason="No active session")
            return

        await websocket.accept()

        # 语言由前端处理，不需要在后端设置
        debug_log(f"WebSocket 连接建立，语言由前端处理: {lang}")

        # 检查会话是否已有 WebSocket 连接
        if session.websocket and session.websocket != websocket:
            debug_log("会话已有 WebSocket 连接，替换为新连接")

        session.websocket = websocket
        debug_log(f"WebSocket 连接建立: 当前活跃会话 {session.session_id}")

        # 发送连接成功消息
        try:
            await websocket.send_json(
                {
                    "type": "connection_established",
                    "messageCode": get_msg_code("websocket_connected"),
                }
            )

            # 检查是否有待发送的会话更新
            if getattr(manager, "_pending_session_update", False):
                debug_log("检测到待发送的会话更新，准备发送通知")
                await websocket.send_json(
                    {
                        "type": "session_updated",
                        "action": "new_session_created",
                        "messageCode": get_msg_code("new_session_created"),
                        "session_info": {
                            "project_directory": session.project_directory,
                            "summary": session.summary,
                            "session_id": session.session_id,
                        },
                    }
                )
                manager._pending_session_update = False
                debug_log("✅ 已发送会话更新通知到前端")
            else:
                # 发送当前会话状态
                await websocket.send_json(
                    {"type": "status_update", "status_info": session.get_status_info()}
                )
                debug_log("已发送当前会话状态到前端")

        except Exception as e:
            debug_log(f"发送连接确认失败: {e}")

        try:
            while True:
                data = await websocket.receive_text()
                message = json.loads(data)

                # 重新获取当前会话，以防会话已切换
                current_session = manager.get_current_session()
                if current_session and current_session.websocket == websocket:
                    await handle_websocket_message(manager, current_session, message)
                else:
                    debug_log("会话已切换或 WebSocket 连接不匹配，忽略消息")
                    break

        except WebSocketDisconnect:
            debug_log("WebSocket 连接正常断开")
        except ConnectionResetError:
            debug_log("WebSocket 连接被重置")
        except Exception as e:
            debug_log(f"WebSocket 错误: {e}")
        finally:
            # 安全清理 WebSocket 连接
            current_session = manager.get_current_session()
            if current_session and current_session.websocket == websocket:
                current_session.websocket = None
                debug_log("已清理会话中的 WebSocket 连接")

    @manager.app.post("/api/save-settings")
    async def save_settings(request: Request):
        """保存设置到文件"""

        try:
            data = await request.json()

            # 使用统一的设置文件路径
            config_dir = Path.home() / ".config" / "mcp-feedback-enhanced"
            config_dir.mkdir(parents=True, exist_ok=True)
            settings_file = config_dir / "ui_settings.json"

            # 保存设置到文件
            with open(settings_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            debug_log(f"设置已保存到: {settings_file}")

            return JSONResponse(
                content={
                    "status": "success",
                    "messageCode": get_msg_code("settings_saved"),
                }
            )

        except Exception as e:
            debug_log(f"保存设置失败: {e}")
            return JSONResponse(
                status_code=500,
                content={
                    "status": "error",
                    "message": f"Save failed: {e!s}",
                    "messageCode": get_msg_code("save_failed"),
                },
            )

    @manager.app.get("/api/load-settings")
    async def load_settings(request: Request):
        """从文件加载设置"""

        try:
            # 使用统一的设置文件路径
            config_dir = Path.home() / ".config" / "mcp-feedback-enhanced"
            settings_file = config_dir / "ui_settings.json"

            if settings_file.exists():
                with open(settings_file, encoding="utf-8") as f:
                    settings = json.load(f)

                debug_log(f"设置已从文件加载: {settings_file}")
                return JSONResponse(content=settings)
            debug_log("设置文件不存在，返回空设置")
            return JSONResponse(content={})

        except Exception as e:
            debug_log(f"加载设置失败: {e}")
            return JSONResponse(
                status_code=500,
                content={
                    "status": "error",
                    "message": f"Load failed: {e!s}",
                    "messageCode": get_msg_code("load_failed"),
                },
            )

    @manager.app.post("/api/clear-settings")
    async def clear_settings(request: Request):
        """清除设置文件"""

        try:
            # 使用统一的设置文件路径
            config_dir = Path.home() / ".config" / "mcp-feedback-enhanced"
            settings_file = config_dir / "ui_settings.json"

            if settings_file.exists():
                settings_file.unlink()
                debug_log(f"设置文件已删除: {settings_file}")
            else:
                debug_log("设置文件不存在，无需删除")

            return JSONResponse(
                content={
                    "status": "success",
                    "messageCode": get_msg_code("settings_cleared"),
                }
            )

        except Exception as e:
            debug_log(f"清除设置失败: {e}")
            return JSONResponse(
                status_code=500,
                content={
                    "status": "error",
                    "message": f"Clear failed: {e!s}",
                    "messageCode": get_msg_code("clear_failed"),
                },
            )

    @manager.app.get("/api/load-session-history")
    async def load_session_history(request: Request):
        """从文件加载会话历史"""

        try:
            # 使用统一的设置文件路径
            config_dir = Path.home() / ".config" / "mcp-feedback-enhanced"
            history_file = config_dir / "session_history.json"

            if history_file.exists():
                with open(history_file, encoding="utf-8") as f:
                    history_data = json.load(f)

                debug_log(f"会话历史已从文件加载: {history_file}")

                # 确保数据格式兼容性
                if isinstance(history_data, dict):
                    # 新格式：包含版本信息和其他元数据
                    sessions = history_data.get("sessions", [])
                    last_cleanup = history_data.get("lastCleanup", 0)
                else:
                    # 旧格式：直接是会话数组（向后兼容）
                    sessions = (
                        history_data if isinstance(history_data, list) else []
                    )
                    last_cleanup = 0

                # 返回会话历史数据
                return JSONResponse(
                    content={
                        "sessions": sessions,
                        "lastCleanup": last_cleanup,
                    }
                )

            debug_log("会话历史文件不存在，返回空历史")
            return JSONResponse(content={"sessions": [], "lastCleanup": 0})

        except Exception as e:
            debug_log(f"加载会话历史失败: {e}")
            return JSONResponse(
                status_code=500,
                content={
                    "status": "error",
                    "message": f"Load failed: {e!s}",
                    "messageCode": get_msg_code("load_failed"),
                },
            )

    @manager.app.post("/api/save-session-history")
    async def save_session_history(request: Request):
        """保存会话历史到文件"""

        try:
            data = await request.json()

            # 使用统一的设置文件路径
            config_dir = Path.home() / ".config" / "mcp-feedback-enhanced"
            config_dir.mkdir(parents=True, exist_ok=True)
            history_file = config_dir / "session_history.json"

            # 建立新格式的数据结构
            history_data = {
                "version": "1.0",
                "sessions": data.get("sessions", []),
                "lastCleanup": data.get("lastCleanup", 0),
                "savedAt": int(time.time() * 1000),  # 当前时间戳
            }

            # 保存会话历史到文件
            with open(history_file, "w", encoding="utf-8") as f:
                json.dump(history_data, f, ensure_ascii=False, indent=2)

            debug_log(f"会话历史已保存到: {history_file}")
            session_count = len(history_data["sessions"])
            debug_log(f"保存了 {session_count} 个会话记录")

            return JSONResponse(
                content={
                    "status": "success",
                    "messageCode": get_msg_code("session_history_saved"),
                    "params": {"count": session_count},
                }
            )

        except Exception as e:
            debug_log(f"保存会话历史失败: {e}")
            return JSONResponse(
                status_code=500,
                content={
                    "status": "error",
                    "message": f"Save failed: {e!s}",
                    "messageCode": get_msg_code("save_failed"),
                },
            )

    @manager.app.get("/api/log-level")
    async def get_log_level(request: Request):
        """获取日志等级设置"""

        try:
            # 使用统一的设置文件路径
            config_dir = Path.home() / ".config" / "mcp-feedback-enhanced"
            settings_file = config_dir / "ui_settings.json"

            if settings_file.exists():
                with open(settings_file, encoding="utf-8") as f:
                    settings_data = json.load(f)
                    log_level = settings_data.get("logLevel", "INFO")
                    debug_log(f"从设置文件加载日志等级: {log_level}")
                    return JSONResponse(content={"logLevel": log_level})
            else:
                # 默认日志等级
                default_log_level = "INFO"
                debug_log(f"使用默认日志等级: {default_log_level}")
                return JSONResponse(content={"logLevel": default_log_level})

        except Exception as e:
            debug_log(f"获取日志等级失败: {e}")
            return JSONResponse(
                status_code=500,
                content={
                    "error": f"Failed to get log level: {e!s}",
                    "messageCode": get_msg_code("get_log_level_failed"),
                },
            )

    @manager.app.post("/api/log-level")
    async def set_log_level(request: Request):
        """设置日志等级"""

        try:
            data = await request.json()
            log_level = data.get("logLevel")

            if not log_level or log_level not in [
                "DEBUG",
                "INFO",
                "WARN",
                "ERROR",
            ]:
                return JSONResponse(
                    status_code=400,
                    content={
                        "error": "Invalid log level",
                        "messageCode": get_msg_code("invalid_log_level"),
                    },
                )

            # 使用统一的设置文件路径
            config_dir = Path.home() / ".config" / "mcp-feedback-enhanced"
            config_dir.mkdir(parents=True, exist_ok=True)
            settings_file = config_dir / "ui_settings.json"

            # 加载现有设置或创建新设置
            settings_data = {}
            if settings_file.exists():
                with open(settings_file, encoding="utf-8") as f:
                    settings_data = json.load(f)

            # 更新日志等级
            settings_data["logLevel"] = log_level

            # 保存设置到文件
            with open(settings_file, "w", encoding="utf-8") as f:
                json.dump(settings_data, f, ensure_ascii=False, indent=2)

            debug_log(f"日志等级已设置为: {log_level}")

            return JSONResponse(
                content={
                    "status": "success",
                    "logLevel": log_level,
                    "messageCode": get_msg_code("log_level_updated"),
                }
            )

        except Exception as e:
            debug_log(f"设置日志等级失败: {e}")
            return JSONResponse(
                status_code=500,
                content={
                    "status": "error",
                    "message": f"Set failed: {e!s}",
                    "messageCode": get_msg_code("set_failed"),
                },
            )


async def handle_websocket_message(manager: "WebUIManager", session, data: dict):
    """处理 WebSocket 消息"""
    message_type = data.get("type")

    if message_type == "submit_feedback":
        # 提交回馈
        feedback = data.get("feedback", "")
        images = data.get("images", [])
        settings = data.get("settings", {})
        await session.submit_feedback(feedback, images, settings)

    elif message_type == "run_command":
        # 执行命令
        command = data.get("command", "")
        if command.strip():
            await session.run_command(command)

    elif message_type == "get_status":
        # 获取会话状态
        if session.websocket:
            try:
                await session.websocket.send_json(
                    {"type": "status_update", "status_info": session.get_status_info()}
                )
            except Exception as e:
                debug_log(f"发送状态更新失败: {e}")

    elif message_type == "heartbeat":
        # WebSocket 心跳处理（简化版）
        # 更新心跳时间
        session.last_heartbeat = time.time()
        session.last_activity = time.time()

        # 发送心跳回应
        if session.websocket:
            try:
                await session.websocket.send_json(
                    {
                        "type": "heartbeat_response",
                        "timestamp": data.get("timestamp", 0),
                    }
                )
            except Exception as e:
                debug_log(f"发送心跳回应失败: {e}")

    elif message_type == "user_timeout":
        # 用户设置的超时已到
        debug_log(f"收到用户超时通知: {session.session_id}")
        # 清理会话资源
        await session._cleanup_resources_on_timeout()
        # 重构：不再自动停止服务器，保持服务器运行以支持持久性

    elif message_type == "pong":
        # 处理来自前端的 pong 回应（用于连接检测）
        debug_log(f"收到 pong 回应，时间戳: {data.get('timestamp', 'N/A')}")
        # 可以在这里记录延迟或更新连接状态

    elif message_type == "update_timeout_settings":
        # 处理超时设置更新
        settings = data.get("settings", {})
        debug_log(f"收到超时设置更新: {settings}")
        if settings.get("enabled"):
            session.update_timeout_settings(
                enabled=True, timeout_seconds=settings.get("seconds", 3600)
            )
        else:
            session.update_timeout_settings(enabled=False)

    else:
        debug_log(f"未知的消息类型: {message_type}")


async def _delayed_server_stop(manager: "WebUIManager"):
    """延迟停止服务器"""
    import asyncio

    await asyncio.sleep(5)  # 等待 5 秒让前端有时间关闭
    from ..main import stop_web_ui

    stop_web_ui()
    debug_log("Web UI 服务器已因用户超时而停止")
