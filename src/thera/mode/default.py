"""
默认活动：增量式被动观察
"""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def split_paragraphs(content: str) -> list[str]:
    """段落切分：按空行切分，过滤空字符串"""
    paragraphs = content.split("\n\n")
    return [p.strip() for p in paragraphs if p.strip()]


def is_already_annotated(text: str) -> bool:
    """检测是否已添加批注"""
    return "🤖 观察者注" in text


def is_short(text: str) -> bool:
    """判断段落是否过短（<20字）"""
    return len(text.strip()) < 20


def read_file(file_path: str) -> str:
    """读取文件"""
    with open(file_path, encoding="utf-8") as f:
        return f.read()


def write_file(file_path: str, content: str) -> str:
    """写入文件"""
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(content)
    return file_path


class JournalProcessor:
    """日志处理器"""

    def __init__(self, llm_client: LLMClient | None = None):
        self.llm = llm_client or LLMClient()

    def process(self, file_path: str) -> str:
        """处理日志文件"""
        # 1. 读取文件
        content = read_file(file_path)

        # 2. 段落切分
        paragraphs = split_paragraphs(content)
        new_content_parts = []

        # 3. 处理每个段落
        for para in paragraphs:
            # 跳过已处理的段落
            if is_already_annotated(para):
                new_content_parts.append(para)
                continue

            # 跳过过短段落
            if is_short(para):
                new_content_parts.append(para)
                continue

            # 调用 LLM 获取批注
            try:
                annotation = self.llm.get_annotation(para)
            except Exception as e:
                logger.error(f"获取批注失败: {e}")
                new_content_parts.append(para)
                continue

            # 追加批注
            if annotation and annotation != "SKIP":
                updated_para = f"{para}\n\n{annotation}"
                new_content_parts.append(updated_para)
            else:
                new_content_parts.append(para)

        # 4. 全量写回，保证原子性
        result_content = "\n\n".join(new_content_parts)
        write_file(file_path, result_content)

        logger.info(f"处理完成: {file_path}")
        return file_path


class LLMClient:
    """LLM 客户端"""

    def __init__(self):
        from thera.config import settings

        self.opencode_path = settings.opencode_path

    def get_annotation(self, text: str) -> str:
        """调用 opencode 获取批注"""
        import subprocess

        prompt = self._build_prompt(text)

        try:
            result = subprocess.run(
                [self.opencode_path, "run", prompt],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                return result.stdout.strip()
            else:
                logger.error(f"OpenCode 调用失败: {result.stderr}")
                return "SKIP"

        except subprocess.TimeoutExpired:
            logger.error("OpenCode 调用超时")
            return "SKIP"
        except Exception as e:
            logger.error(f"OpenCode 调用异常: {e}")
            return "SKIP"

    def _build_prompt(self, text: str) -> str:
        """构建 Prompt"""
        return f"""阅读以下段落，判断其核心价值。

段落内容：
{text}

如果它只是无意义的闲聊或过渡语，请输出：SKIP

如果它包含洞察、决策或风险，请按以下格式输出批注（使用引用语法 >）：
> 🤖 观察者注
> 🏷️ 标签：<分类1> <分类2>
> 💎 提炼：<提取的标准化知识>
> ⚠️ 状态：<状态说明>
> 🔗 关联：<关联说明>
> 🔑 关键：<关键要点>
> 🔄 模式：<模式说明>

注意：
1. 只输出批注内容，不要修改原文
2. 标签使用 # 前缀
3. 提炼要简洁，不超过 50 字
4. 非必填项可省略"""
