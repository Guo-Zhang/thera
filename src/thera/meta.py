"""
ADAS 模型核心模块

- Activity: 当前执行流（动态）
- Domain: 知识边界（静态）
- Asset: 信息实体（内容）
- State: 元数据属性（状态）
"""

from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path

# State - 状态管理
from thera.state.storage_state import StorageState


# Domain - 知识领域
class DomainType(Enum):
    THINK = "think"
    WRITE = "write"
    KNOWL = "knowl"
    CONNECT = "connect"


class Domain(ABC):
    """Domain - 知识边界，划定知识检索的命名空间"""

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

    def auto_switch(self, user_input: str) -> DomainType | None:
        return None


class DomainManager:
    """Domain 管理器"""

    def __init__(self, app):
        self.app = app
        self._domains: dict = {}
        self._current_domain: Domain | None = None

    def register(self, domain_type: str, domain_class):
        self._domains[domain_type] = domain_class

    def register_default_domains(self):
        from thera.domain.connect_domain import ConnectDomain
        from thera.domain.knowl_domain import KnowlDomain
        from thera.domain.think_domain import ThinkDomain
        from thera.domain.write_domain import WriteDomain

        self.register("think", ThinkDomain)
        self.register("write", WriteDomain)
        self.register("knowl", KnowlDomain)
        self.register("connect", ConnectDomain)

    def switch_domain(self, domain_type: str):
        if self._current_domain:
            self._current_domain.on_deactivate()

        if domain_type not in self._domains:
            raise ValueError(f"Unknown domain: {domain_type}")

        domain_class = self._domains[domain_type]
        self._current_domain = domain_class(self.app)
        self._current_domain.on_activate()
        return self._current_domain

    def get_current_domain(self) -> Domain | None:
        return self._current_domain

    def handle_input(self, user_input: str) -> str:
        if not self._current_domain:
            return "No domain selected. Use /domain <name> to select a domain."

        suggested = self._current_domain.auto_switch(user_input)
        if suggested:
            domain_type = suggested.value
            if domain_type in self._domains:
                self.switch_domain(domain_type)
                return f"[Switched to {domain_type} domain]"

        return self._current_domain.handle_input(user_input)
