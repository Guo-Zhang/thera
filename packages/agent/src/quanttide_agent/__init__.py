"""
quanttide-agent - AIGC 基础设施

包含：
- LLM 调用（chat, stream, json_request 等）
- Embeddings 向量计算
- 相似度算法（jaccard, keyword, tfidf, embedding）
- 聚类算法
- 关键词提取
"""

__version__ = "0.1.0"

from .llm import (
    create_client,
    chat,
    chat_str,
    stream,
    json_request,
)
from .embedding import (
    get_embeddings,
    get_embedding,
    embedding_similarity,
    embedding_similarity_matrix,
)
from .similarity import (
    jaccard_similarity,
    keyword_similarity,
    tfidf_similarity,
)
from .cluster import (
    cluster_notes,
    compute_cluster_centroids,
    find_bridge_notes,
    find_cross_cluster_links,
)
from .analysis import (
    extract_keywords,
    extract_triplets,
    summarize_content,
    evaluate_content_quality,
    evaluate_ttl_quality,
    analyze_development_direction,
    deduplicate_entities,
    classify_and_draft,
)

__all__ = [
    "create_client",
    "chat",
    "chat_str",
    "stream",
    "json_request",
    "get_embeddings",
    "get_embedding",
    "embedding_similarity",
    "embedding_similarity_matrix",
    "jaccard_similarity",
    "keyword_similarity",
    "tfidf_similarity",
    "cluster_notes",
    "compute_cluster_centroids",
    "find_bridge_notes",
    "find_cross_cluster_links",
    "extract_keywords",
    "extract_triplets",
    "summarize_content",
    "evaluate_content_quality",
    "evaluate_ttl_quality",
    "analyze_development_direction",
    "deduplicate_entities",
    "classify_and_draft",
]
