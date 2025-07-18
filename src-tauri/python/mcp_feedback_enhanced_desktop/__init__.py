#!/usr/bin/env python3
"""
MCP Feedback Enhanced Desktop Application
=========================================

基于 Tauri 的桌面应用程序包装器，为 MCP Feedback Enhanced 提供原生桌面体验。

主要功能：
- 原生桌面应用程序界面
- 整合现有的 Web UI 功能
- 跨平台支持（Windows、macOS、Linux）
- 无需浏览器的独立运行环境

作者: Minidoracat
版本: 2.4.3
"""

__version__ = "2.4.3"
__author__ = "Minidoracat"
__email__ = "minidora0702@gmail.com"

from .desktop_app import DesktopApp, launch_desktop_app


__all__ = [
    "DesktopApp",
    "__author__",
    "__version__",
    "launch_desktop_app",
]
