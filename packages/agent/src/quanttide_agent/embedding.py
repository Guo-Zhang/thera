"""
嵌入向量模块
"""

from typing import List

import numpy as np
from openai import OpenAI

from .config import get_settings
from .llm import create_client


def get_embeddings(texts: list[str], batch_size: int = 10) -> list[list[float]]:
    """获取文本嵌入向量"""
    client = create_client()
    settings = get_settings()

    all_embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        response = client.embeddings.create(
            model=settings.llm_embedding_model,
            input=batch,
        )
        all_embeddings.extend([d.embedding for d in response.data])

    return all_embeddings


def get_embedding(text: str) -> list[float]:
    """获取单个文本的嵌入向量"""
    return get_embeddings([text])[0]


def embedding_similarity_matrix(embeddings: list[list[float]]) -> np.ndarray:
    """计算嵌入向量相似度矩阵"""
    return embedding_similarity(np.array(embeddings))


def embedding_similarity(embeddings: np.ndarray) -> np.ndarray:
    """基于嵌入向量的余弦相似度"""
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    normalized = embeddings / (norms + 1e-8)
    return np.dot(normalized, normalized.T)
