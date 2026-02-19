"""
系统元信息模块

用于观察和描述系统自身的状态和属性
"""

from typing import Any
from datetime import datetime


def get_system_info() -> dict[str, Any]:
    """获取系统信息"""
    return {
        "name": "thera",
        "version": "0.1.0",
        "description": "AI Assistant",
    }


def get_timestamp() -> str:
    """获取当前时间戳"""
    return datetime.now().isoformat()


class SystemState:
    """系统状态快照"""

    def __init__(self):
        self.started_at = datetime.now()
        self.command_count = 0

    def record_command(self):
        self.command_count += 1

    def snapshot(self) -> dict[str, Any]:
        return {
            "started_at": self.started_at.isoformat(),
            "command_count": self.command_count,
            "uptime_seconds": (datetime.now() - self.started_at).total_seconds(),
        }


_system_state = SystemState()


def get_system_state() -> SystemState:
    return _system_state
