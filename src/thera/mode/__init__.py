"""知识图谱模块"""


def get_knowl_functions():
    """延迟导入 knowl 模块函数"""
    from .knowl import (
        compute_all_similarities,
        build_similarity_report,
        cluster_notes,
        extract_keywords,
        generate_report,
        get_embeddings,
        embedding_similarity_matrix,
    )

    return {
        "compute_all_similarities": compute_all_similarities,
        "build_similarity_report": build_similarity_report,
        "cluster_notes": cluster_notes,
        "extract_keywords": extract_keywords,
        "generate_report": generate_report,
        "get_embeddings": get_embeddings,
        "embedding_similarity_matrix": embedding_similarity_matrix,
    }
