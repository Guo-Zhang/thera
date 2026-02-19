"""
相似度算法模块
"""

import re

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def jaccard_similarity(text1: str, text2: str) -> float:
    """基于 n-gram 的 Jaccard 相似度"""

    def get_ngrams(text: str, n: int = 3) -> set:
        text = re.sub(r"\s+", "", text.lower())
        return set(text[i : i + n] for i in range(len(text) - n + 1))

    ngrams1 = get_ngrams(text1)
    ngrams2 = get_ngrams(text2)

    if not ngrams1 or not ngrams2:
        return 0.0

    intersection = len(ngrams1 & ngrams2)
    union = len(ngrams1 | ngrams2)
    return intersection / union if union > 0 else 0.0


def tfidf_similarity(texts: list[str]) -> np.ndarray:
    """基于 TF-IDF 的余弦相似度"""
    vectorizer = TfidfVectorizer(analyzer="char", ngram_range=(2, 4), max_features=5000)
    tfidf_matrix = vectorizer.fit_transform(texts)
    return cosine_similarity(tfidf_matrix)


def keyword_similarity(text1: str, text2: str) -> float:
    """基于关键词的 Jaccard 相似度"""

    def extract_keywords(text: str) -> set:
        text = re.sub(r"[^\w\u4e00-\u9fff]", " ", text)
        words = text.split()
        return set(w for w in words if len(w) >= 2)

    kw1 = extract_keywords(text1)
    kw2 = extract_keywords(text2)

    if not kw1 or not kw2:
        return 0.0

    intersection = len(kw1 & kw2)
    union = len(kw1 | kw2)
    return intersection / union
