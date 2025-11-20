#!/usr/bin/env python3
"""
MCP Feedback Enhanced Desktop Application
=========================================

基於 Tauri 的桌面應用程式包裝器，為 MCP Feedback Enhanced 提供原生桌面體驗。

主要功能：
- 原生桌面應用程式界面
- 整合現有的 Web UI 功能
- 跨平台支援（Windows、macOS、Linux）
- 無需瀏覽器的獨立運行環境

作者: jayzqj
版本: 使用统一版本管理 (见主项目 _version.py)
"""

# 从统一版本文件导入版本信息
# 注意：这里需要相对路径导入主项目的版本文件
import sys
from pathlib import Path

# 添加主项目路径到 sys.path
main_project_path = Path(__file__).parent.parent.parent.parent / "src"
sys.path.insert(0, str(main_project_path))

try:
    from mcp_feedback_enhanced._version import __version__, __author__, __email__
except ImportError:
    # 如果导入失败，使用默认值
    __version__ = "2025.828.1"
    __author__ = "jayzqj"
    __email__ = ""

from .desktop_app import DesktopApp, launch_desktop_app


__all__ = [
    "DesktopApp",
    "__author__",
    "__version__",
    "launch_desktop_app",
]
