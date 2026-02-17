# Domain 依赖分析报告

- **生成时间**: 2026-02-18 01:34:04

## 1. Domain 概览

| Domain | 类 | 函数数 | 导入数 |
| --- | --- | --- | --- |
| write | WriteDomain | 4 | 2 |
| connect | AuthoritySource, ConfirmationStatus, Context, ConnectDomain | 10 | 3 |
| think | IdeaCategory, ThinkDomain | 11 | 5 |
| knowl | DocType, KnowlDomain | 20 | 33 |

## 2. 导入依赖详情

### write

**Thera 内部导入:**
- `thera.meta.Domain`
- `thera.meta.DomainType`

### connect

**Thera 内部导入:**
- `thera.meta.Domain`
- `thera.meta.DomainType`

**标准库/第三方导入:** 1 个

### think

**Thera 内部导入:**
- `thera.meta.Domain`
- `thera.meta.DomainType`

**标准库/第三方导入:** 2 个

### knowl

**Thera 内部导入:**
- `thera.config.settings`
- `thera.infra.ai.llm_chat_str`
- `thera.infra.ai.extract_keywords`
- `thera.infra.ai.extract_triplets`
- `thera.infra.ai.find_bridge_notes`
- `thera.infra.ai.find_cross_cluster_links`
- `thera.infra.ai.get_embedding`
- `thera.infra.ai.get_embeddings`
- `thera.infra.ai.llm_json_request`
- `thera.infra.ai.llm_stream`
- `thera.meta.Domain`
- `thera.meta.DomainType`
- `thera.infra.ai.embedding_similarity`
- `thera.infra.ai.get_embeddings`
- `thera.infra.ai.jaccard_similarity`
- `thera.infra.ai.keyword_similarity`
- `thera.infra.ai.tfidf_similarity`
- `thera.infra.ai._cluster_notes`
- `thera.infra.ai._extract_keywords`
- `thera.infra.ai._compute_cluster_centroids`
- `thera.infra.ai._find_bridge_notes`
- `thera.infra.ai._find_cross_cluster_links`

**标准库/第三方导入:** 7 个


## 3. 依赖图

_无显式 Domain 间导入依赖_

## 4. 循环依赖检测

✅ **无循环依赖**

## 5. 跨 Domain 调用

- connect -> _handle_connect
- knowl -> write_text
- knowl -> write
- knowl -> write
- knowl -> write

## 6. 分析洞察

- **依赖最多**: knowl (29 个导入)

**外部依赖:**
- connect: enum
- think: datetime, enum
- knowl: collections, datetime, enum, openai, pathlib, typing