#!/usr/bin/env python3
"""
MCP Feedback Enhanced 服务器主要模块

此模块提供 MCP (Model Context Protocol) 的增强反馈收集功能，
支持智能环境检测，自动使用 Web UI 界面。

主要功能：
- MCP 工具实现
- 界面选择（Web UI）
- 环境检测 (SSH Remote, WSL, Local)
- 国际化支持
- 图片处理与上传
- 命令执行与结果展示
- 项目目录管理

主要 MCP 工具：
- interactive_feedback: 收集用户互动反馈
- get_system_info: 获取系统环境信息

作者: Fábio Ferreira (原作者)
增强: Minidoracat (Web UI, 图片支持, 环境检测)
重构: 模块化设计
"""

import base64
import io
import json
import os
import sys
from typing import Annotated, Any

from fastmcp import FastMCP
from mcp.types import TextContent
from pydantic import Field

# 导入统一的调试功能
from .debug import server_debug_log as debug_log

# 导入多语系支持
# 导入错误处理框架
from .utils.error_handler import ErrorHandler, ErrorType

# 导入资源管理器
from .utils.resource_manager import create_temp_file


# ===== 编码初始化 =====
def init_encoding():
    """初始化编码设置，确保正确处理中文字符"""
    try:
        # Windows 特殊处理
        if sys.platform == "win32":
            import msvcrt

            # 设置为二进制模式
            msvcrt.setmode(sys.stdin.fileno(), os.O_BINARY)
            msvcrt.setmode(sys.stdout.fileno(), os.O_BINARY)

            # 重新包装为 UTF-8 文本流，并禁用缓冲
            # 修复 union-attr 错误 - 安全获取 buffer 或 detach
            stdin_buffer = getattr(sys.stdin, "buffer", None)
            if stdin_buffer is None and hasattr(sys.stdin, "detach"):
                stdin_buffer = sys.stdin.detach()

            stdout_buffer = getattr(sys.stdout, "buffer", None)
            if stdout_buffer is None and hasattr(sys.stdout, "detach"):
                stdout_buffer = sys.stdout.detach()

            sys.stdin = io.TextIOWrapper(
                stdin_buffer, encoding="utf-8", errors="replace", newline=None
            )
            sys.stdout = io.TextIOWrapper(
                stdout_buffer,
                encoding="utf-8",
                errors="replace",
                newline="",
                write_through=True,  # 关键：禁用写入缓冲
            )
        else:
            # 非 Windows 系统的标准设置
            if hasattr(sys.stdout, "reconfigure"):
                sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            if hasattr(sys.stdin, "reconfigure"):
                sys.stdin.reconfigure(encoding="utf-8", errors="replace")

        # 设置 stderr 编码（用于调试消息）
        if hasattr(sys.stderr, "reconfigure"):
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")

        return True
    except Exception:
        # 如果编码设置失败，尝试基本设置
        try:
            if hasattr(sys.stdout, "reconfigure"):
                sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            if hasattr(sys.stdin, "reconfigure"):
                sys.stdin.reconfigure(encoding="utf-8", errors="replace")
            if hasattr(sys.stderr, "reconfigure"):
                sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except:
            pass
        return False


# 初始化编码（在导入时就执行）
_encoding_initialized = init_encoding()

# ===== 常数定义 =====
SERVER_NAME = "互动式反馈收集 MCP"
SSH_ENV_VARS = ["SSH_CONNECTION", "SSH_CLIENT", "SSH_TTY"]
REMOTE_ENV_VARS = ["REMOTE_CONTAINERS", "CODESPACES"]


# 初始化 MCP 服務器
from . import __version__


# 确保 log_level 设定为正确的大写格式
fastmcp_settings = {}

# 检查环境变量并设定正确的 log_level
env_log_level = os.getenv("FASTMCP_LOG_LEVEL", "").upper()
if env_log_level in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"):
    fastmcp_settings["log_level"] = env_log_level
else:
    # 默认使用 INFO 等级
    fastmcp_settings["log_level"] = "INFO"

mcp: Any = FastMCP(SERVER_NAME)


# ===== 工具函数 =====
def is_wsl_environment() -> bool:
    """
    检测是否在 WSL (Windows Subsystem for Linux) 环境中运行

    Returns:
        bool: True 表示 WSL 环境，False 表示其他环境
    """
    try:
        # 检查 /proc/version 文件是否包含 WSL 标识
        if os.path.exists("/proc/version"):
            with open("/proc/version") as f:
                version_info = f.read().lower()
                if "microsoft" in version_info or "wsl" in version_info:
                    debug_log("检测到 WSL 环境（通过 /proc/version）")
                    return True

        # 检查 WSL 相关环境变量
        wsl_env_vars = ["WSL_DISTRO_NAME", "WSL_INTEROP", "WSLENV"]
        for env_var in wsl_env_vars:
            if os.getenv(env_var):
                debug_log(f"检测到 WSL 环境变量: {env_var}")
                return True

        # 检查是否存在 WSL 特有的路径
        wsl_paths = ["/mnt/c", "/mnt/d", "/proc/sys/fs/binfmt_misc/WSLInterop"]
        for path in wsl_paths:
            if os.path.exists(path):
                debug_log(f"检测到 WSL 特有路径: {path}")
                return True

    except Exception as e:
        debug_log(f"WSL 检测过程中发生错误: {e}")

    return False


def is_remote_environment() -> bool:
    """
    检测是否在远程环境中运行

    Returns:
        bool: True 表示远程环境，False 表示本地环境
    """
    # WSL 不应被视为远程环境，因为它可以访问 Windows 浏览器
    if is_wsl_environment():
        debug_log("WSL 环境不被视为远程环境")
        return False

    # 检查 SSH 连线指标
    for env_var in SSH_ENV_VARS:
        if os.getenv(env_var):
            debug_log(f"检测到 SSH 环境变量: {env_var}")
            return True

    # 检查远程开发环境
    for env_var in REMOTE_ENV_VARS:
        if os.getenv(env_var):
            debug_log(f"检测到远程开发环境: {env_var}")
            return True

    # 检查 Docker 容器
    if os.path.exists("/.dockerenv"):
        debug_log("检测到 Docker 容器环境")
        return True

    # Windows 远程桌面检查
    if sys.platform == "win32":
        session_name = os.getenv("SESSIONNAME", "")
        if session_name and "RDP" in session_name:
            debug_log(f"检测到 Windows 远程桌面: {session_name}")
            return True

    # Linux 无显示环境检查（但排除 WSL）
    if (
        sys.platform.startswith("linux")
        and not os.getenv("DISPLAY")
        and not is_wsl_environment()
    ):
        debug_log("检测到 Linux 无显示环境")
        return True

    return False


def save_feedback_to_file(feedback_data: dict, file_path: str | None = None) -> str:
    """
    将反馈资料保存到 JSON 文件

    Args:
        feedback_data: 反馈资料字典
        file_path: 保存路径，若为 None 则自动产生临时文件

    Returns:
        str: 保存的文件路径
    """
    if file_path is None:
        # 使用资源管理器创建临时文件
        file_path = create_temp_file(suffix=".json", prefix="feedback_")

    # 确保目录存在
    directory = os.path.dirname(file_path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)

    # 复制数据以避免修改原始数据
    json_data = feedback_data.copy()

    # 处理图片数据：将 bytes 转换为 base64 字符串以便 JSON 序列化
    if "images" in json_data and isinstance(json_data["images"], list):
        processed_images = []
        for img in json_data["images"]:
            if isinstance(img, dict) and "data" in img:
                processed_img = img.copy()
                # 如果 data 是 bytes，转换为 base64 字符串
                if isinstance(img["data"], bytes):
                    processed_img["data"] = base64.b64encode(img["data"]).decode(
                        "utf-8"
                    )
                    processed_img["data_type"] = "base64"
                processed_images.append(processed_img)
            else:
                processed_images.append(img)
        json_data["images"] = processed_images

    # 保存资料
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)

    debug_log(f"反馈资料已保存至: {file_path}")
    return file_path


def create_feedback_text(feedback_data: dict) -> str:
    """
    建立格式化的反馈文字

    Args:
        feedback_data: 反馈资料字典

    Returns:
        str: 格式化后的反馈文字
    """
    text_parts = []

    # 基本反馈内容
    if feedback_data.get("interactive_feedback"):
        text_parts.append(f"=== 用户反馈 ===\n{feedback_data['interactive_feedback']}")

    # 命令执行日志
    if feedback_data.get("command_logs"):
        text_parts.append(f"=== 命令执行日志 ===\n{feedback_data['command_logs']}")

    # 图片附件概要
    if feedback_data.get("images"):
        images = feedback_data["images"]
        text_parts.append(f"=== 图片附件概要 ===\n用户提供了 {len(images)} 张图片：")

        for i, img in enumerate(images, 1):
            size = img.get("size", 0)
            name = img.get("name", "unknown")

            # 智能单位显示
            if size < 1024:
                size_str = f"{size} B"
            elif size < 1024 * 1024:
                size_kb = size / 1024
                size_str = f"{size_kb:.1f} KB"
            else:
                size_mb = size / (1024 * 1024)
                size_str = f"{size_mb:.1f} MB"

            img_info = f"  {i}. {name} ({size_str})"

            # 为提高兼容性，添加 base64 预览信息
            if img.get("data"):
                try:
                    if isinstance(img["data"], bytes):
                        img_base64 = base64.b64encode(img["data"]).decode("utf-8")
                    elif isinstance(img["data"], str):
                        img_base64 = img["data"]
                    else:
                        img_base64 = None

                    if img_base64:
                        # 只显示前50个字符的预览
                        preview = (
                            img_base64[:50] + "..."
                            if len(img_base64) > 50
                            else img_base64
                        )
                        img_info += f"\n     Base64 预览: {preview}"
                        img_info += f"\n     完整 Base64 长度: {len(img_base64)} 字符"

                        # 如果 AI 助手不支持 MCP 图片，可以提供完整 base64
                        debug_log(f"图片 {i} Base64 已准备，长度: {len(img_base64)}")

                        # 检查是否启用 Base64 详细模式（从 UI 设定中获取）
                        include_full_base64 = feedback_data.get("settings", {}).get(
                            "enable_base64_detail", False
                        )

                        if include_full_base64:
                            # 根据文件名推断 MIME 类型
                            file_name = img.get("name", "image.png")
                            if file_name.lower().endswith((".jpg", ".jpeg")):
                                mime_type = "image/jpeg"
                            elif file_name.lower().endswith(".gif"):
                                mime_type = "image/gif"
                            elif file_name.lower().endswith(".webp"):
                                mime_type = "image/webp"
                            else:
                                mime_type = "image/png"

                            img_info += f"\n     完整 Base64: data:{mime_type};base64,{img_base64}"

                except Exception as e:
                    debug_log(f"图片 {i} Base64 处理失败: {e}")

            text_parts.append(img_info)

        # 添加兼容性说明
        text_parts.append(
            "\n💡 注意：如果 AI 助手无法显示图片，图片数据已包含在上述 Base64 信息中。"
        )

    return "\n\n".join(text_parts) if text_parts else "用户未提供任何反馈内容。"


# 注意：不再需要 process_images 函数，因为我们不直接返回 MCPImage 对象
# 图片数据通过 create_feedback_text() 函数包含在文本内容中


# ===== MCP 工具定义 =====
@mcp.tool()
async def interactive_feedback(
    project_directory: Annotated[str, Field(description="项目目录路径")] = ".",
    summary: Annotated[
        str, Field(description="AI 工作完成的摘要说明")
    ] = "我已完成了您请求的任务。",
    timeout: Annotated[int, Field(description="等待用户反馈的超时时间（秒）")] = 6000,
) -> list:
    """Interactive feedback collection tool for LLM agents.

    USAGE RULES:
    1. During any process, task, or conversation, whether asking, replying, or completing phased tasks, you must call this tool to ask for feedback.
    2. Unless receiving termination instructions, all steps must repeatedly call this tool.
    3. Whenever user feedback is received, if the feedback content is not empty, you must call this tool again and adjust behavior based on the feedback content.
    4. Only when the user explicitly indicates "end" or "no more interaction needed" can you stop calling this tool, and the process is considered complete.
    5. You should summarize what have done, and provide project directory through args to let user know what you have done to provide feedback for next step.

    Args:
        project_directory: Project directory path for context
        summary: Summary of AI work completed for user review
        timeout: Timeout in seconds for waiting user feedback (default: 6000 seconds)

    Returns:
        list: List containing TextContent and MCPImage objects representing user feedback
    """
    # 环境检测
    is_remote = is_remote_environment()
    is_wsl = is_wsl_environment()

    debug_log(f"环境检测结果 - 远程: {is_remote}, WSL: {is_wsl}")
    debug_log("使用界面: Web UI")

    try:
        # 确保项目目录存在
        if not os.path.exists(project_directory):
            project_directory = os.getcwd()
        project_directory = os.path.abspath(project_directory)

        # 使用 Web 模式
        debug_log("反馈模式: web")

        result = await launch_web_feedback_ui(project_directory, summary, timeout)

        # 处理取消情况
        if not result:
            return [TextContent(type="text", text="用户取消了反馈。")]

        # 保存详细结果
        save_feedback_to_file(result)

        # 建立反馈项目列表
        feedback_items = []

        # 添加文字反馈
        if (
            result.get("interactive_feedback")
            or result.get("command_logs")
            or result.get("images")
        ):
            feedback_text = create_feedback_text(result)
            feedback_items.append(TextContent(type="text", text=feedback_text))
            debug_log("文字反馈已添加")

        # 注意：不直接添加 MCPImage 对象，因为 FastMCP 无法序列化
        # 图片数据已经包含在 create_feedback_text() 生成的文本中
        if result.get("images"):
            debug_log(f"图片数据已包含在文本反馈中，共 {len(result['images'])} 张图片")

        # 确保至少有一个反馈项目
        if not feedback_items:
            feedback_items.append(
                TextContent(type="text", text="用户未提供任何反馈内容。")
            )

        debug_log(f"反馈收集完成，共 {len(feedback_items)} 个项目")
        return feedback_items

    except Exception as e:
        # 使用统一错误处理，但不影响 JSON RPC 响应
        error_id = ErrorHandler.log_error_with_context(
            e,
            context={"operation": "反馈收集", "project_dir": project_directory},
            error_type=ErrorType.SYSTEM,
        )

        # 生成用户友好的错误信息
        user_error_msg = ErrorHandler.format_user_error(e, include_technical=False)
        debug_log(f"反馈收集错误 [错误ID: {error_id}]: {e!s}")

        return [TextContent(type="text", text=user_error_msg)]


async def launch_web_feedback_ui(project_dir: str, summary: str, timeout: int) -> dict:
    """
    启动 Web UI 收集反馈，支持自定义超时时间

    Args:
        project_dir: 项目目录路径
        summary: AI 工作摘要
        timeout: 超时时间（秒）

    Returns:
        dict: 收集到的反馈资料
    """
    debug_log(f"启动 Web UI 界面，超时时间: {timeout} 秒")

    try:
        # 使用新的 web 模块
        from .web import launch_web_feedback_ui as web_launch

        # 传递 timeout 参数给 Web UI
        return await web_launch(project_dir, summary, timeout)
    except ImportError as e:
        # 使用统一错误处理
        error_id = ErrorHandler.log_error_with_context(
            e,
            context={"operation": "Web UI 模块导入", "module": "web"},
            error_type=ErrorType.DEPENDENCY,
        )
        user_error_msg = ErrorHandler.format_user_error(
            e, ErrorType.DEPENDENCY, include_technical=False
        )
        debug_log(f"Web UI 模块导入失败 [错误ID: {error_id}]: {e}")

        return {
            "command_logs": "",
            "interactive_feedback": user_error_msg,
            "images": [],
        }


@mcp.tool()
def get_system_info() -> str:
    """
    获取系统环境信息

    Returns:
        str: JSON 格式的系统信息
    """
    is_remote = is_remote_environment()
    is_wsl = is_wsl_environment()

    system_info = {
        "平台": sys.platform,
        "Python 版本": sys.version.split()[0],
        "WSL 环境": is_wsl,
        "远程环境": is_remote,
        "界面类型": "Web UI",
        "环境变量": {
            "SSH_CONNECTION": os.getenv("SSH_CONNECTION"),
            "SSH_CLIENT": os.getenv("SSH_CLIENT"),
            "DISPLAY": os.getenv("DISPLAY"),
            "VSCODE_INJECTION": os.getenv("VSCODE_INJECTION"),
            "SESSIONNAME": os.getenv("SESSIONNAME"),
            "WSL_DISTRO_NAME": os.getenv("WSL_DISTRO_NAME"),
            "WSL_INTEROP": os.getenv("WSL_INTEROP"),
            "WSLENV": os.getenv("WSLENV"),
        },
    }

    return json.dumps(system_info, ensure_ascii=False, indent=2)


# ===== 主程序入口 =====
def main():
    """主要入口点，用于套件执行
    收集用户的互动反馈，支持文字和图片
    此工具使用 Web UI 界面收集用户反馈，支持智能环境检测。

    用户可以：
    1. 执行命令来验证结果
    2. 提供文字反馈
    3. 上传图片作为反馈
    4. 查看 AI 的工作摘要

    调试模式：
    - 设置环境变量 MCP_DEBUG=true 可启用详细调试输出
    - 生产环境建议关闭调试模式以避免输出干扰


    """
    # 检查是否启用调试模式
    debug_enabled = os.getenv("MCP_DEBUG", "").lower() in ("true", "1", "yes", "on")

    # 检查是否启用桌面模式
    desktop_mode = os.getenv("MCP_DESKTOP_MODE", "").lower() in (
        "true",
        "1",
        "yes",
        "on",
    )

    if debug_enabled:
        debug_log("🚀 启动互动式反馈收集 MCP 服务器")
        debug_log(f"   服务器名称: {SERVER_NAME}")
        debug_log(f"   版本: {__version__}")
        debug_log(f"   平台: {sys.platform}")
        debug_log(f"   编码初始化: {'成功' if _encoding_initialized else '失败'}")
        debug_log(f"   远程环境: {is_remote_environment()}")
        debug_log(f"   WSL 环境: {is_wsl_environment()}")
        debug_log(f"   桌面模式: {'启用' if desktop_mode else '禁用'}")
        debug_log("   界面类型: Web UI")
        debug_log("   等待来自 AI 助手的调用...")
        debug_log("准备启动 MCP 服务器...")
        debug_log("调用 mcp.run()...")

    try:
        # 使用正确的 FastMCP API
        mcp.run()
    except KeyboardInterrupt:
        if debug_enabled:
            debug_log("收到中断信号，正常退出")
        sys.exit(0)
    except Exception as e:
        if debug_enabled:
            debug_log(f"MCP 服务器启动失败: {e}")
            import traceback

            debug_log(f"详细错误: {traceback.format_exc()}")
        sys.exit(1)


if __name__ == "__main__":
    main()
