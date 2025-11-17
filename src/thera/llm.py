"""
大模型调用模块

thera.llm
=================

封装 DeepSeek（或兼容 OpenAI 接口的模型）和 Graphiti 功能的客户端。

提供:
- DeepSeekClient: 轻量封装，使用 openai 包调用聊天/Completion 接口。
- GraphitiClient: 集成 Graphiti 知识图谱功能的增强客户端。

设计目标：最小、可测、提供 Graphiti 知识图谱集成功能。
"""

import os
from typing import Optional, List, Dict, Any
import asyncio
from datetime import datetime

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    OpenAI = None

try:
    from graphiti_core import Graphiti
    from graphiti_core.driver.neo4j_driver import Neo4jDriver
    from graphiti_core.llm_client.openai_generic_client import OpenAIGenericClient
    from graphiti_core.llm_client.config import LLMConfig
    from graphiti_core.embedder.openai import OpenAIEmbedder, OpenAIEmbedderConfig
    from graphiti_core.cross_encoder.openai_reranker_client import OpenAIRerankerClient
    GRAPHITI_AVAILABLE = True
except ImportError:
    GRAPHITI_AVAILABLE = False
    Graphiti = Neo4jDriver = OpenAIGenericClient = LLMConfig = None
    OpenAIEmbedder = OpenAIEmbedderConfig = OpenAIRerankerClient = None

from .config import settings


class DeepSeekClient:
    """A thin wrapper around an OpenAI-compatible chat/completion model.

    It reads the model name from environment settings and the API key from environment.
    A custom `api_key` or `base_url` can be passed to override environment settings.

    Usage:
        client = DeepSeekClient()
        text = client.generate("请帮我写一段关于深度学习的简介。")
    """

    def __init__(self, model: Optional[str] = None, api_key: Optional[str] = None,
                 base_url: Optional[str] = None):
        if not OPENAI_AVAILABLE:
            raise RuntimeError("OpenAI package is not installed")

        self.model = model or settings.llm_model
        self.api_key = api_key or settings.llm_api_key
        self.base_url = base_url or settings.llm_base_url

        if not self.api_key:
            raise RuntimeError("LLM_API_KEY is not set; provide api_key or set environment variable")

        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    def generate(self, prompt: str, max_tokens: int = 512, temperature: float = 0.0,
                 stream: bool = False) -> str:
        """Generate a completion from the model.

        Args:
            prompt: the user prompt / input text.
            max_tokens: maximum tokens to generate.
            temperature: sampling temperature.
            stream: whether to stream the response.

        Returns:
            The generated text (stripped).

        Raises:
            ValueError: if prompt is empty or not a string.
            RuntimeError: if model returns no content.
        """
        if not prompt or not isinstance(prompt, str):
            raise ValueError("prompt must be a non-empty string")

        if stream:
            return self._generate_stream(prompt, max_tokens, temperature)

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=temperature,
        )

        return (response.choices[0].message.content or "").strip()

    def _generate_stream(self, prompt: str, max_tokens: int, temperature: float) -> str:
        """Stream generate completion from the model."""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=temperature,
            stream=True
        )

        full_response = ""
        for chunk in response:
            if not chunk.choices:
                continue
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                print(content, end="", flush=True)
                full_response += content
            if hasattr(chunk.choices[0].delta, 'reasoning_content') and chunk.choices[0].delta.reasoning_content:
                reasoning = chunk.choices[0].delta.reasoning_content
                print(reasoning, end="", flush=True)
                full_response += reasoning

        return full_response.strip()


class GraphitiClient:
    """集成 Graphiti 知识图谱功能的增强客户端。

    提供知识图谱的增删改查功能，集成 LLM 能力进行智能搜索。
    """

    def __init__(self):
        if not GRAPHITI_AVAILABLE:
            raise RuntimeError("Graphiti packages are not installed")

        # Graphiti 配置
        self.graph_driver = Neo4jDriver(
            uri=settings.neo4j_uri,
            user=settings.neo4j_user,
            password=settings.neo4j_password,
            database=settings.neo4j_database,
        )

        llm_config = LLMConfig(
            api_key=settings.llm_api_key,
            base_url=settings.llm_base_url,
            model=settings.llm_model,
        )

        embedder_config = OpenAIEmbedderConfig(
            api_key=settings.llm_api_key,
            embedding_model=settings.llm_embedding_model,
            base_url=settings.llm_base_url,
        )

        reranker_config = LLMConfig(
            api_key=settings.llm_api_key,
            model=settings.llm_reranker_model,
            base_url=settings.llm_base_url,
        )

        # 初始化 Graphiti 客户端
        self.graphiti = Graphiti(
            graph_driver=self.graph_driver,
            llm_client=OpenAIGenericClient(config=llm_config),
            embedder=OpenAIEmbedder(config=embedder_config),
            cross_encoder=OpenAIRerankerClient(config=reranker_config),
        )

    async def initialize(self):
        """初始化 Graphiti 客户端和索引"""
        await self.graphiti.build_indices_and_constraints()
        print("Graphiti 客户端初始化成功!")

    async def add_episode(self, name: str, episode_body: str, source_description: str,
                         reference_time: datetime = None):
        """添加事件到知识图谱"""
        if reference_time is None:
            reference_time = datetime.now()

        await self.graphiti.add_episode(
            name=name,
            episode_body=episode_body,
            source_description=source_description,
            reference_time=reference_time,
        )

    async def search(self, query: str) -> List[Dict[str, Any]]:
        """在知识图谱中搜索"""
        results = await self.graphiti.search(query=query)

        formatted_results = []
        for result in results:
            formatted_results.append({
                'uuid': result.uuid,
                'fact': result.fact,
                'valid_at': getattr(result, 'valid_at', None),
                'invalid_at': getattr(result, 'invalid_at', None)
            })

        return formatted_results

    async def close(self):
        """关闭 Graphiti 客户端"""
        await self.graphiti.close()

    async def __aenter__(self):
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

