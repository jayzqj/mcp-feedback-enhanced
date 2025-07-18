#!/usr/bin/env python3
"""
测试配置和共用 fixtures
"""

import asyncio
import os
import shutil
import tempfile
from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest

# 使用正确的模块导入，不手动修改 sys.path
from mcp_feedback_enhanced.i18n import get_i18n_manager
from mcp_feedback_enhanced.web.main import WebUIManager


@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环 fixture"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """创建临时目录 fixture"""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture
def test_project_dir(temp_dir: Path) -> Path:
    """创建测试项目目录"""
    project_dir = temp_dir / "test_project"
    project_dir.mkdir()

    # 创建一些测试文件
    (project_dir / "README.md").write_text("# Test Project")
    (project_dir / "main.py").write_text("print('Hello World')")

    return project_dir


@pytest.fixture
def web_ui_manager() -> Generator[WebUIManager, None, None]:
    """创建 WebUIManager fixture"""
    import os

    # 设置测试模式环境变量
    original_test_mode = os.environ.get("MCP_TEST_MODE")
    original_web_host = os.environ.get("MCP_WEB_HOST")
    original_web_port = os.environ.get("MCP_WEB_PORT")

    os.environ["MCP_TEST_MODE"] = "true"
    os.environ["MCP_WEB_HOST"] = "127.0.0.1"  # 确保测试使用本地主机
    # 使用动态端口范围避免冲突
    os.environ["MCP_WEB_PORT"] = "0"  # 让系统自动分配端口

    try:
        manager = WebUIManager()  # 使用环境变量控制主机和端口
        yield manager
    finally:
        # 恢复原始环境变量
        if original_test_mode is not None:
            os.environ["MCP_TEST_MODE"] = original_test_mode
        else:
            os.environ.pop("MCP_TEST_MODE", None)

        if original_web_host is not None:
            os.environ["MCP_WEB_HOST"] = original_web_host
        else:
            os.environ.pop("MCP_WEB_HOST", None)

        if original_web_port is not None:
            os.environ["MCP_WEB_PORT"] = original_web_port
        else:
            os.environ.pop("MCP_WEB_PORT", None)

        # 清理
        if manager.server_thread and manager.server_thread.is_alive():
            # 这里可以添加服务器停止逻辑
            pass


@pytest.fixture
def i18n_manager():
    """创建 I18N 管理器 fixture"""
    return get_i18n_manager()


@pytest.fixture
def test_config() -> dict[str, Any]:
    """测试配置 fixture"""
    return {
        "timeout": 30,
        "debug": True,
        "web_port": 8765,
        "test_summary": "测试摘要 - 这是一个自动化测试",
        "test_feedback": "这是测试回馈内容",
    }


@pytest.fixture(autouse=True)
def setup_test_env():
    """自动设置测试环境"""
    # 设置测试环境变量
    original_debug = os.environ.get("MCP_DEBUG")
    os.environ["MCP_DEBUG"] = "true"

    yield

    # 恢复原始环境
    if original_debug is not None:
        os.environ["MCP_DEBUG"] = original_debug
    else:
        os.environ.pop("MCP_DEBUG", None)
