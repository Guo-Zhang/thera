# 备忘录活动开发逻辑

## 概述

分析苹果备忘录数据，从中发现知识分组和关键概念，输出知识图谱 TTL 格式，并评估知识质量。

## 输入输出

- **输入**: `data/infra/apple/notes.json`
- **输出**: 
  - `vectors.json` - 嵌入向量和相似度矩阵
  - `knowledge.ttl` - 知识图谱
  - `跨组关联.json` - 跨分组关联
  - `术语映射表.json` - 实体消歧映射
  - `知识卡片草稿.json` - 卡片草稿
  - `知识卡片集.md` - Markdown 格式卡片集
  - `报告.md` - 内容介绍
  - `评估.md` - 质量评估
  - `复盘.md` - 经验总结

## 算法流程

### 1. 语义嵌入向量

使用 OpenAI Embedding API 获取文本的语义向量：

```python
client = create_llm_client()
embedding = get_embedding(text, client)
```

### 2. 语义相似度

使用余弦相似度计算笔记之间的语义相似度：

```python
similarity = cosine_similarity(embedding1, embedding2)
```

### 3. 分组（聚类）

基于相似度阈值进行聚类：

```python
clusters = cluster_notes(similarity_matrix, threshold=0.5)
```

### 4. 知识图谱抽取

使用 LLM 从每个分组中提取知识图谱三元组：

```python
ttl_triplets = extract_triplets(client, cluster_notes)
```

### 5. 跨组关联发现

计算分组质心向量，找出不同分组之间的潜在关联：

```python
cross_links = find_cross_cluster_links(embeddings, clusters, notes)
# 输出: [{"group_a": 1, "group_b": 4, "similarity": 0.45, "bridge_notes": [...]}]
```

### 6. 实体消歧与合并

使用 LLM 统一实体命名：

```python
dedup_result = deduplicate_entities(client, combined_ttl)
# 输出: {"canonical_entities": [...], "mapping": {"别名": "标准名称"}}
```

### 7. 意图分类与卡片生成

识别笔记意图类型，生成结构化知识卡片：

```python
card_results = batch_classify_notes(client, notes)
# 意图类型: Definition, Action, Case, Question, Insight
```

### 8. 质量评估

使用 LLM 评估知识图谱质量：

```python
quality = evaluate_ttl_quality(client, ttl_content, titles)
# 评估维度: completeness, accuracy, coherence
```

## 可配置参数

```python
run_memo_activity(
    notes_file=None,              # 输入文件路径
    output_dir=None,              # 输出目录
    similarity_threshold=0.5,   # 相似度阈值
    enable_quality_check=True,   # 是否启用质量评估
)
```

## 模块化设计

- `create_llm_client()`: 创建 LLM 客户端
- `get_embedding()`: 获取嵌入向量
- `compute_embeddings()`: 批量计算嵌入
- `cosine_similarity()`: 计算余弦相似度
- `cluster_notes()`: 基于阈值的聚类
- `extract_triplets()`: 提取知识图谱三元组
- `find_cross_cluster_links()`: 发现跨组关联
- `deduplicate_entities()`: 实体消歧
- `classify_and_draft_note()`: 意图分类与卡片生成
- `evaluate_ttl_quality()`: 评估知识图谱质量
