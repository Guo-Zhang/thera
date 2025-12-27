# reasoner.py
import json
from .models import Method, Memory

class Reasoner:
    @staticmethod
    def reason(method: Method, memory: Memory) -> dict:
        # 实际项目中这里调用 LLM
        # 但在测试中我们希望注入模拟响应
        # 所以提取 llm_call 为独立函数便于 mock
        raw_input = memory.content.get("raw", "")
        prompt = method.prompt_template.format(raw_input=raw_input)
        llm_response = Reasoner._call_llm(prompt)
        try:
            return json.loads(llm_response)
        except json.JSONDecodeError:
            return {}

    @staticmethod
    def _call_llm(prompt: str) -> str:
        # 实际调用 Qwen API 的地方
        raise NotImplementedError("Production implementation required")