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

# 初始化 Graphiti 客户端
graphiti = Graphiti(
    graph_driver=graph_driver,
    llm_client=OpenAIGenericClient(config=llm_config),
    embedder=OpenAIEmbedder(config=embedder_config),
    cross_encoder=OpenAIRerankerClient(config=reranker_config),
)

async def test_graphiti():
    await graphiti.add_episode(
        name="员工信息",
        episode_body=("张三是资深Python工程师 有5年开发经验。"),
        source_description="人力资源系统",
        reference_time=datetime(2025, 11, 15, 9, 30),
    )
