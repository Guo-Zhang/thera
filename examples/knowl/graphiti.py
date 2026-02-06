#!/usr/bin/env python3
"""
简化版 Graphiti 示例程序
"""

import asyncio
from datetime import datetime
   
from graphiti_core import Graphiti
from graphiti_core.driver.neo4j_driver import Neo4jDriver
from graphiti_core.llm_client.openai_generic_client import OpenAIGenericClient
from graphiti_core.llm_client.config import LLMConfig
from graphiti_core.embedder.openai import OpenAIEmbedder, OpenAIEmbedderConfig
from graphiti_core.cross_encoder.openai_reranker_client import OpenAIRerankerClient

from examples.knowl.config import settings


# Graphiti配置
graph_driver = Neo4jDriver(
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


async def main():
    """主函数，演示 Graphiti 的基本用法"""

    # 初始化 Graphiti 客户端
    graphiti = Graphiti(
        graph_driver=graph_driver,
        llm_client=OpenAIGenericClient(config=llm_config),
        embedder=OpenAIEmbedder(config=embedder_config),
        cross_encoder=OpenAIRerankerClient(config=reranker_config),
    )
    await graphiti.build_indices_and_constraints()

    print("Graphiti 客户端初始化成功!")
    
    # 添加示例数据到知识图谱
    print("添加示例数据...")
    
    await graphiti.add_episode(
        name="员工信息",
        episode_body=("张三是资深Python工程师 有5年开发经验。"),
        source_description="人力资源系统",
        reference_time=datetime(2025, 11, 15, 9, 30),
    )
    
    await graphiti.add_episode(
        name="项目信息",
        episode_body=("李四负责AI助手项目 他是数据科学专家。"),
        source_description="项目管理系统",
        reference_time=datetime(2025, 11, 15, 9, 40),
    )
    
    # 执行搜索查询
    print("执行搜索查询...")
    query = "哪个工程师有Python经验?"
    results = await graphiti.search(query=query)
    
    print(f"查询 '{query}' 的结果:")

    for result in results:
        print(f'UUID: {result.uuid}')
        print(f'Fact: {result.fact}')
        if hasattr(result, 'valid_at') and result.valid_at:
            print(f'Valid from: {result.valid_at}')
        if hasattr(result, 'invalid_at') and result.invalid_at:
            print(f'Valid until: {result.invalid_at}')
        print('---')

    # 关闭 Graphiti 客户端
    await graphiti.close()
    print("Graphiti 客户端已关闭。")


if __name__ == "__main__":
    asyncio.run(main())
