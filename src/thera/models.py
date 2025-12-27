# domain.py (或你的实际模块)
from dataclasses import dataclass
from typing import Dict, Any

@dataclass(frozen=True)  # 值对象：不可变
class Method:
    name: str
    prompt_template: str = ""

@dataclass
class Memory:
    id: str
    content: Dict[str, Any]
    source: str = "unknown"
