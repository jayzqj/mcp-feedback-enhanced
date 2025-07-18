#!/usr/bin/env python3
"""
MCP 客户端模拟器 - 简化版本
"""

import asyncio
import json
import subprocess
from pathlib import Path
from typing import Any

from .test_utils import PerformanceTimer


class SimpleMCPClient:
    """简化的 MCP 客户端模拟器"""

    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.server_process: subprocess.Popen | None = None
        self.stdin: Any = None
        self.stdout: Any = None
        self.stderr: Any = None
        self.initialized = False

    async def start_server(self) -> bool:
        """启动 MCP 服务器"""
        try:
            # 使用正确的 uv run 命令启动 MCP 服务器
            cmd = ["uv", "run", "python", "-m", "mcp_feedback_enhanced"]

            self.server_process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=0,
                cwd=Path.cwd(),
                encoding="utf-8",  # 明确指定 UTF-8 编码
                errors="replace",  # 处理编码错误
            )

            self.stdin = self.server_process.stdin
            self.stdout = self.server_process.stdout
            self.stderr = self.server_process.stderr

            # 等待服务器启动
            await asyncio.sleep(2)

            if self.server_process.poll() is not None:
                return False

            return True

        except Exception as e:
            print(f"启动 MCP 服务器失败: {e}")
            return False

    async def initialize(self) -> bool:
        """初始化 MCP 连接"""
        if not self.server_process or self.server_process.poll() is not None:
            return False

        try:
            # 发送初始化请求
            init_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "roots": {"listChanged": True}, 
                        "sampling": {}
                    },
                    "clientInfo": {"name": "test-client", "version": "1.0.0"},
                },
            }

            await self._send_request(init_request)
            response = await self._read_response()

            if response and "result" in response:
                self.initialized = True
                return True

        except Exception as e:
            print(f"MCP 初始化失败: {e}")

        return False

    async def call_interactive_feedback(
        self, project_directory: str, summary: str, timeout: int = 30
    ) -> dict[str, Any]:
        """调用 interactive_feedback 工具"""
        if not self.initialized:
            return {"error": "MCP 客户端未初始化"}

        try:
            request = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "interactive_feedback",
                    "arguments": {
                        "project_directory": project_directory,
                        "summary": summary,
                        "timeout": timeout,
                    },
                },
            }

            with PerformanceTimer() as timer:
                await self._send_request(request)
                response = await self._read_response(timeout=timeout + 5)

            if response and "result" in response:
                result = response["result"]
                result["performance"] = {"duration": timer.duration}
                # 修复 no-any-return 错误 - 确保返回明确类型
                return dict(result)  # 明确返回 dict[str, Any] 类型
            return {"error": "无效的回应格式", "response": response}

        except TimeoutError:
            return {"error": "调用超时"}
        except Exception as e:
            return {"error": f"调用失败: {e!s}"}

    async def _send_request(self, request: dict[str, Any]):
        """发送请求"""
        if not self.stdin:
            raise RuntimeError("stdin 不可用")

        request_str = json.dumps(request) + "\n"
        self.stdin.write(request_str)
        self.stdin.flush()

    async def _read_response(self, timeout: int = 30) -> dict[str, Any] | None:
        """读取回应"""
        if not self.stdout:
            raise RuntimeError("stdout 不可用")

        try:
            # 使用 asyncio 超时
            response_line = await asyncio.wait_for(
                asyncio.to_thread(self.stdout.readline), timeout=timeout
            )

            if response_line:
                response_data = json.loads(response_line.strip())
                # 修复 no-any-return 错误 - 确保返回明确类型
                return (
                    dict(response_data)
                    if isinstance(response_data, dict)
                    else response_data
                )
            return None

        except TimeoutError:
            raise
        except json.JSONDecodeError as e:
            print(f"JSON 解析错误: {e}, 原始数据: {response_line}")
            return None

    async def cleanup(self):
        """清理资源"""
        if self.server_process:
            try:
                # 尝试正常终止
                self.server_process.terminate()

                # 等待进程结束
                try:
                    await asyncio.wait_for(
                        asyncio.to_thread(self.server_process.wait), timeout=5
                    )
                except TimeoutError:
                    # 强制终止
                    self.server_process.kill()
                    await asyncio.to_thread(self.server_process.wait)

            except Exception as e:
                print(f"清理 MCP 服务器失败: {e}")
            finally:
                self.server_process = None
                self.stdin = None
                self.stdout = None
                self.stderr = None
                self.initialized = False


class MCPWorkflowTester:
    """MCP 工作流程测试器"""

    def __init__(self, timeout: int = 60):
        self.timeout = timeout
        self.client = SimpleMCPClient(timeout)

    async def test_basic_workflow(
        self, project_dir: str, summary: str
    ) -> dict[str, Any]:
        """测试基本工作流程"""
        result: dict[str, Any] = {
            "success": False,
            "steps": {},
            "errors": [],
            "performance": {},
        }

        with PerformanceTimer() as timer:
            try:
                # 1. 启动服务器
                if await self.client.start_server():
                    result["steps"]["server_started"] = True
                else:
                    result["errors"].append("服务器启动失败")
                    return result

                # 2. 初始化连接
                if await self.client.initialize():
                    result["steps"]["initialized"] = True
                else:
                    result["errors"].append("初始化失败")
                    return result

                # 3. 调用 interactive_feedback
                feedback_result = await self.client.call_interactive_feedback(
                    project_dir, summary, timeout=10
                )

                if "error" not in feedback_result:
                    result["steps"]["interactive_feedback_called"] = True
                    result["feedback_result"] = feedback_result
                    result["success"] = True
                else:
                    result["errors"].append(
                        f"interactive_feedback 调用失败: "
                        f"{feedback_result['error']}"
                    )

            except Exception as e:
                result["errors"].append(f"测试异常: {e!s}")
            finally:
                await self.client.cleanup()
                result["performance"]["total_duration"] = timer.duration

        return result
