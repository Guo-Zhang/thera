# 备忘录活动开发逻辑

## 概述

分析苹果备忘录数据，从中发现知识分组和关键概念，输出知识图谱 TTL 格式，并评估知识质量。

## 输入输出

- **输入**: `data/infra/apple/notes.json`
- **输出**: 
  - `data/activity/memo/analysis.json` - 分析结果（兼容旧版本）
  - `data/activity/memo/knowledge.ttl` - 知识图谱
  - `data/activity/memo/report.json` - 分析报告（含质量评估）

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

### 5. 质量评估

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
    similarity_threshold=0.5,     # 相似度阈值
    enable_quality_check=True,   # 是否启用质量评估
)
```

## 模块化设计

- `create_llm_client()`: 创建 LLM 客户端，可替换为其他实现
- `get_embedding()`: 获取嵌入向量
- `extract_triplets()`: 提取三元组
- `evaluate_ttl_quality()`: 评估质量

## 后续优化方向

1. **改进聚类算法** - 使用 K-Means 或层次聚类
2. **增加摘要生成** - 使用 LLM 生成更准确的摘要
3. **支持更多评估维度** - 如新颖性、实用性等
