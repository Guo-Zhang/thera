---
name: extracting
title: 提取现实→虚构地点映射
author: iGuo
components:
  - Method
  - Memory
  - Reasoner
testable: true
---

# {title}

## 目标

从用户自由输入的原始想法中，自动识别并结构化存储“现实地点 → 虚构地点”的映射关系，作为维护小说内部逻辑一致性的基础。

## 过程（How it works）

本部分描述系统内部如何协作完成该用例，面向开发者、架构师或希望理解机制的创作者。


## 捕获输入

用户在命令行中输入：
```text
我想写一个以滁州为原型的小说，在小说中以滁州的别名“亭城”为名，实际写作的时候会增加很多虚构。
```

系统将其封装为临时 Memory 实体（source: "user_input"）。

### 选择策略

应用层识别该输入可能包含“地点映射”，选择预定义的推理策略：
```python
method = Method(name="extract_location_mapping")
```

### 调用推理器

执行领域服务：

```python
output = Reasoner.reason(method=method, memory=temp_memory)
```

### LLM 推理执行

Reasoner 使用以下提示模板（来自 Method.prompt_template）调用大模型 API：

```
{literalinclude} 
:language: text
```

模型返回结构化 JSON 响应。

### 结构化存储

系统验证输出格式后，创建正式 Memory 实体，并存入图数据库，建立如下关系：

```cypher
(r:RealLocation {name: "滁州"})-[:MAPPED_TO {type: "prototype"}]->(f:FictionalLocation {name: "亭城"})
```

### 反馈与可视化

UI 在“虚实映射看板”中新增一条记录，并向用户显示友好确认消息。


## 结果（What is produced）

本部分描述用例成功执行后产生的可观测、可验证的输出，面向创作者、测试人员或 AI 验证代理。

### ✅ 成功场景：明确映射被提取

生成的记忆条目（持久化 Memory 实体）：
```
{literalinclude} ./fixtures/uc01_expected_memory.json
:language: json
```

用户界面反馈：
✅ 已识别映射：滁州 → 亭城（原型关系）
可在 [虚实映射看板](#) 中查看或编辑。

图数据库状态变更（可用于集成测试断言）：
```cypher
MATCH (r:RealLocation {name: "滁州"})-[:MAPPED_TO]->(f:FictionalLocation {name: "亭城"})
RETURN count(*) = 1 AS mapping_exists
```

### ⚠️ 异常场景

- "故事发生在一个模糊的南方小城。" LLM 无法提取有效映射 → 系统提示："❓ 未能识别明确地点映射。是否手动指定？"
- 再次提交"滁州 → 亭城" 系统检测到重复映射 → 显示："该映射已存在，是否添加备注？"（不创建新 Memory）
- 输入格式混乱（如无地名） 返回空结果，记录日志，不中断流程


## 🧪 可测试性

- 输入 fixture：./fixtures/uc01_user_input.txt
- 期望输出 fixture：./fixtures/uc01_expected_memory.json
- 测试类型：集成测试（覆盖 Reasoner + LLM 模拟 + Memory 存储）
- 自动化建议：使用 pytest + pytest-myst 或自定义解析器加载本用例元数据生成测试用例。
