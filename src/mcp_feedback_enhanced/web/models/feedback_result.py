#!/usr/bin/env python3
"""
回馈结果数据模型

定义回馈收集的数据结构，用于 Web UI 与后端的数据传输。
"""

from typing import TypedDict


class FeedbackResult(TypedDict):
    """回馈结果的类型定义"""

    command_logs: str
    interactive_feedback: str
    images: list[dict]
