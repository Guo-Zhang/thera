"""
Activity 管理器
"""

from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path

from thera.meta import Domain


class ActivityType(Enum):
    CHAT = "chat"
    THINK = "think"
    WRITE = "write"
    KNOWL = "knowl"
    CONNECT = "connect"


class Activity(ABC):
    """Activity - 当前执行流"""

    name: str = ""
    description: str = ""

    def __init__(self, app):
        self.app = app

    @abstractmethod
    def handle_input(self, user_input: str) -> str:
        pass

    @abstractmethod
    def on_activate(self):
        pass

    @abstractmethod
    def on_deactivate(self):
        pass

    def auto_switch(self, user_input: str) -> ActivityType | None:
        return None


class ActivityManager:
    """Activity 管理器"""

    def __init__(self, app):
        self.app = app
        self._activities: dict = {}
        self._current_activity: Activity | None = None

    def register(self, activity_type: str, activity_class):
        self._activities[activity_type] = activity_class

    def register_default_activities(self):
        from thera.activity.default_activity import DefaultActivity as ChatActivity
        from thera.domain.think_domain import ThinkDomain
        from thera.domain.write_domain import WriteDomain
        from thera.domain.knowl_domain import KnowlDomain
        from thera.domain.connect_domain import ConnectDomain

        # Chat 是默认 Activity，也是 Domain
        self.register("chat", ChatActivity)
        self.register("think", ThinkDomain)
        self.register("write", WriteDomain)
        self.register("knowl", KnowlDomain)
        self.register("connect", ConnectDomain)

    def switch_activity(self, activity_type: str):
        if self._current_activity:
            self._current_activity.on_deactivate()

        if activity_type not in self._activities:
            raise ValueError(f"Unknown activity: {activity_type}")

        activity_class = self._activities[activity_type]
        self._current_activity = activity_class(self.app)
        self._current_activity.on_activate()
        return self._current_activity

    def get_current_activity(self) -> Activity | None:
        return self._current_activity

    def handle_input(self, user_input: str) -> str:
        if not self._current_activity:
            return "No activity selected. Use /activity <name> to select an activity."
        return self._current_activity.handle_input(user_input)

    def auto_switch(self, user_input: str) -> ActivityType | None:
        """自动切换检测"""
        if not self._current_activity:
            return None
        return self._current_activity.auto_switch(user_input)
