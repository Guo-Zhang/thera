"""
聚类算法模块
"""

from typing import Any, List

import numpy as np


def cluster_notes(
    similarity_matrix: List[List[float]],
    threshold: float = 0.5,
) -> List[List[int]]:
    """根据相似度阈值聚类"""
    n = len(similarity_matrix)
    visited = [False] * n
    clusters = []

    for i in range(n):
        if visited[i]:
            continue

        cluster = [i]
        visited[i] = True

        for j in range(i + 1, n):
            if not visited[j] and similarity_matrix[i][j] > threshold:
                cluster.append(j)
                visited[j] = True

        if len(cluster) > 1:
            clusters.append(cluster)

    return clusters


def compute_cluster_centroids(
    embeddings: List[List[float]], clusters: List[List[int]]
) -> List[List[float]]:
    """计算每个聚类的质心"""
    embeddings_array = np.array(embeddings)
    centroids = []
    for cluster in clusters:
        cluster_embeddings = embeddings_array[cluster]
        centroid = cluster_embeddings.mean(axis=0).tolist()
        centroids.append(centroid)
    return centroids


def find_bridge_notes(
    embeddings: List[List[float]], clusters: List[List[int]], threshold: float = 0.3
) -> List[dict[str, Any]]:
    """找出连接不同聚类的桥接笔记"""
    embeddings_array = np.array(embeddings)
    centroids = compute_cluster_centroids(embeddings, clusters)
    n_clusters = len(clusters)

    if n_clusters < 2:
        return []

    bridge_notes = []
    for i, cluster in enumerate(clusters):
        for note_idx in cluster:
            note_embedding = embeddings_array[note_idx]
            similarities = []
            for j, centroid in enumerate(centroids):
                if i == j:
                    continue
                sim = np.dot(note_embedding, centroid) / (
                    np.linalg.norm(note_embedding) * np.linalg.norm(centroid) + 1e-8
                )
                similarities.append((j, sim))

            max_sim = max(similarities, key=lambda x: x[1])
            if max_sim[1] > threshold:
                bridge_notes.append(
                    {
                        "note_index": note_idx,
                        "from_cluster": i,
                        "to_cluster": max_sim[0],
                        "similarity": float(max_sim[1]),
                    }
                )

    return bridge_notes


def find_cross_cluster_links(
    embeddings: List[List[float]], clusters: List[List[int]], top_n: int = 3
) -> List[dict[str, Any]]:
    """找出跨聚类的高相似度连接"""
    embeddings_array = np.array(embeddings)
    n_clusters = len(clusters)
    cross_links = []

    for i in range(n_clusters):
        for j in range(i + 1, n_clusters):
            cluster_i_embeddings = embeddings_array[clusters[i]]
            cluster_j_embeddings = embeddings_array[clusters[j]]

            sim_matrix = np.dot(cluster_i_embeddings, cluster_j_embeddings.T)
            sim_matrix = sim_matrix / (
                np.linalg.norm(cluster_i_embeddings, axis=1, keepdims=True)
                * np.linalg.norm(cluster_j_embeddings, axis=1, keepdims=True).T
                + 1e-8
            )

            for _ in range(top_n):
                max_idx = np.unravel_index(np.argmax(sim_matrix), sim_matrix.shape)
                max_sim = sim_matrix[max_idx]
                if max_sim > 0.5:
                    cross_links.append(
                        {
                            "from_cluster": i,
                            "to_cluster": j,
                            "from_note": clusters[i][max_idx[0]],
                            "to_note": clusters[j][max_idx[1]],
                            "similarity": float(max_sim),
                        }
                    )
                    sim_matrix[max_idx[0], max_idx[1]] = 0
                else:
                    break

    return cross_links
