"""命令处理器"""

from .think import handle as think
from .write import handle as write
from .knowl import handle as knowl
from .connect import handle as connect

__all__ = ["think", "write", "knowl", "connect"]
