"""
Thera 主模块

提供统一的 AI 外脑系统接口，整合 LLM 和 Graphiti 功能。
"""

import asyncio
from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path

from .llm import DeepSeekClient, GraphitiClient
from .config import settings


class Thera:
    """Thera AI 外脑系统主类"""

    def __init__(self):
        self.llm_client = DeepSeekClient()
        self.graphiti_client = GraphitiClient()
        self.initialized = False

    async def initialize(self):
        """初始化 Thera 系统"""
        # 确保 Graphiti 客户端已初始化
        if not self.initialized:
            await self.graphiti_client.initialize()
            self.initialized = True

    async def chat(self, message: str, stream: bool = False) -> str:
        """与 LLM 对话"""
        return self.llm_client.generate(message, stream=stream)

    async def add_knowledge(self, name: str, content: str,
                           source: str = "user_input") -> bool:
        """向知识图谱添加知识"""
        await self.initialize()

        try:
            await self.graphiti_client.add_episode(
                name=name,
                episode_body=content,
                source_description=source,
                reference_time=datetime.now()
            )
            return True
        except Exception as e:
            print(f"添加知识失败: {e}")
            return False

    async def search_knowledge(self, query: str) -> List[Dict[str, Any]]:
        """在知识图谱中搜索"""
        await self.initialize()

        try:
            return await self.graphiti_client.search(query)
        except Exception as e:
            print(f"搜索知识失败: {e}")
            return []

    async def chat_with_knowledge(self, message: str) -> Dict[str, Any]:
        """结合知识图谱进行智能对话"""
        await self.initialize()

        # 先在知识图谱中搜索相关信息
        search_results = await self.search_knowledge(message)

        # 构建增强提示词
        if search_results:
            knowledge_context = "\n".join([
                f"知识 {i+1}: {result['fact']}"
                for i, result in enumerate(search_results[:3])  # 取前3条最相关的结果
            ])

            enhanced_prompt = f"""基于以下知识回答问题：

{knowledge_context}

问题：{message}

请根据上述知识给出准确回答，如果知识不足请说明。"""
        else:
            enhanced_prompt = f"""问题：{message}

请根据你掌握的通用知识回答问题。"""

        # 使用 LLM 生成回答
        response = await self.chat(enhanced_prompt)

        return {
            'response': response,
            'knowledge_references': [r['fact'] for r in search_results[:3]] if search_results else [],
            'total_knowledge_found': len(search_results)
        }

    async def close(self):
        """关闭 Thera 系统"""
        if self.initialized:
            await self.graphiti_client.close()

    async def __aenter__(self):
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


# 便捷的同步函数包装器
def chat_sync(message: str, stream: bool = False) -> str:
    """同步版本的聊天函数"""
    thera = Thera()
    return asyncio.run(thera.chat(message, stream))


def add_knowledge_sync(name: str, content: str, source: str = "user_input") -> bool:
    """同步版本的添加知识函数"""
    thera = Thera()
    return asyncio.run(thera.add_knowledge(name, content, source))


def search_knowledge_sync(query: str) -> List[Dict[str, Any]]:
    """同步版本的搜索知识函数"""
    thera = Thera()
    return asyncio.run(thera.search_knowledge(query))


def chat_with_knowledge_sync(message: str) -> Dict[str, Any]:
    """同步版本的智能对话函数"""
    thera = Thera()
    return asyncio.run(thera.chat_with_knowledge(message))


# 演示函数
async def demo():
    """演示 Thera 系统的功能"""
    async with Thera() as thera:
        print("🎯 Thera AI 外脑系统演示")
        print("=" * 50)

        # 添加示例知识
        print("1. 添加示例知识...")
        await thera.add_knowledge(
            "员工信息",
            "张三是资深Python工程师，有5年开发经验。",
            "示例数据"
        )
        await thera.add_knowledge(
            "项目信息",
            "李四负责AI助手项目，他是数据科学专家。",
            "示例数据"
        )

        # 测试搜索
        print("2. 搜索知识...")
        results = await thera.search_knowledge("Python工程师")
        print(f"找到 {len(results)} 条相关记录")

        # 测试智能对话
        print("3. 智能对话...")
        response = await thera.chat_with_knowledge("哪个工程师有Python经验?")
        print(f"回答: {response['response']}")

        # 测试普通聊天
        print("4. 普通聊天...")
        response = await thera.chat("简单介绍一下机器学习")
        print(f"回答: {response[:100]}...")  # 截取前100字符


if __name__ == "__main__":
    # 运行演示
    asyncio.run(demo())