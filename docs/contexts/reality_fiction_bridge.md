---
title: 虚实之桥
domain: 写作工程

---

# {title}

## 职责

虚实映射(Reality–Fiction Bridge)是管理现实世界元素与小说虚构元素之间的映射关系，确保创作者在“基于现实创作”时，系统能自动维护一致性、避免混淆。

## 目标（Why this context exists）

- 允许作者以真实地点/人物/事件为原型进行虚构创作
- 显式记录“哪些是真实的，哪些是虚构的，如何对应”
- 为其他子域（如时间线检查、人物关系推理）提供可信赖的等价替换规则

## 假设

“亭城 = 滁州” 不是一个事实，而是一个创作约定。
系统必须把它当作可配置、可追溯、可撤销的映射规则来管理。

## 领域模型

### 实体（Entities）

类型 说明
------ ------
RealEntity 现实世界中的事物（地点、人物、机构等）<br>• ID：real:location:chuzhou<br>• 属性：name, type（"location"/"person"）, source_uri（可选，如维基链接）
FictionalEntity 小说中的虚构事物<br>• ID：fiction:location:tingcheng<br>• 属性：name, type, first_mention_chapter
💡 两者均为聚合根（Aggregate Root），各自拥有独立生命周期。

## 值对象（Value Objects）

类型 说明
------ ------
MappingRule 描述映射的语义<br>python<br>@dataclass(frozen=True)<br>class MappingRule:<br> real_id: str<br> fictional_id: str<br> relation_type: Literal["prototype", "symbolic", "composite", "partial"]<br> confidence: float # 可选，用于模糊映射<br>
MappingSource 记录映射来源<br>• user_input / reasoner_inference / imported_doc
✅ MappingRule 是不可变的值对象——一旦创建，不能修改；要“更新”就创建新版本。

## 🔺 聚合设计

[ Reality–Fiction Bridge 聚合 ]
│
├── RealEntity (AR)
├── FictionalEntity (AR)
└── MappingRegistry (领域服务，非聚合根)
└── 维护 {real_id → [fictional_id]} 的索引（供查询用）
⚠️ 不变性约束（Invariants）：
同一 fictional_id 不能同时映射到两个不同的 real_id（除非 relation_type="composite"）
删除 RealEntity 时，应级联标记相关映射为“失效”（而非直接删除，保留历史）

## 3️⃣ 领域服务 & 事件
🧩 领域服务

服务 职责
------ ------
MappingExtractor 接收原始文本，调用 Reasoner，生成 MappingRule 候选
ConsistencyGuard 提供方法：<br>resolve_fictional_to_real(name: str) -> Optional[str]<br>供 Timeline 或 Character 上下文调用

## 📢 领域事件（Domain Events）

事件 触发时机
------ --------
MappingProposed(real_id, fictional_id, rule) 用户或 AI 提出新映射
MappingConfirmed(mapping_rule) 用户确认后持久化
MappingInvalidated(mapping_rule, reason) 因冲突或编辑被废弃
🔄 这些事件可被 Timeline Consistency 上下文监听，用于重建“真实地理位置时间线”。

## 4️⃣ 与其他限界上下文的关系（Context Map）

mermaid
graph LR
A[Reality–Fiction Bridge] --> 提供 resolve() B[Narrative Timeline]
A --> 提供 alias list C[Character Network]
D[User Interface] --> 提交原始文本 A
E[Reasoner Service] --> 输出候选映射 A
A -.-> 发布 MappingConfirmed F[Audit Log]

协作模式说明：

目标上下文 协作方式 集成机制
----------- -------- --------
Narrative Timeline 查询“亭城的真实位置”以检测时空冲突 调用 ConsistencyGuard.resolve_fictional_to_real("亭城") → 返回 "滁州"
Character Network 判断“角色A的故乡=亭城”是否与“角色B的故乡=南京”冲突 同上，依赖映射解析
Audit Log 记录所有映射变更 订阅 MappingConfirmed 事件
Reasoner 提供候选映射 通过 MappingProposed 事件异步提交
🔒 防腐层（Anti-Corruption Layer）：
Timeline 上下文不直接访问 Bridge 的内部模型，只通过 resolve() 接口获取结果，避免模型污染。

## 5️⃣ 如何支撑你的核心需求？

### ✅ 保证逻辑一致性
当 Timeline 检查“1998年主角在亭城” vs “1998年在南京”时，
→ 通过 Bridge 得知 亭城 ≡ 滁州 ≠ 南京 → 判定无冲突
若用户后来将“亭城”改为映射“合肥”，
→ 所有历史事件自动重新解释（或触发警告）

### ✅ 区分现实/虚构/映射
RealEntity：代表客观存在（可链接外部知识库）
FictionalEntity：代表小说设定（可自由编辑）
MappingRule：代表作者的创作选择（可版本化）

### ✅ 维护“桥梁”
所有映射显式存储，可追溯、可审查、可回滚
支持“多对一”（多个虚构地名指向同一现实原型）、“一对多”（一个现实拆成多个虚构区域）

6️⃣ 示例：一次完整交互

用户输入：
“我把老家滁州写成了小说里的亭城，但西街改成了滨河路。”

系统行为：
1. MappingExtractor 识别：
RealEntity("滁州") ←→ FictionalEntity("亭城") （relation: prototype）
RealEntity("滁州/西街") ←→ FictionalEntity("亭城/滨河路") （relation: modified）
2. 创建两条 MappingRule，触发 MappingProposed 事件
3. UI 显示：“检测到2处映射，是否确认？”
4. 用户确认 → 发布 MappingConfirmed
5. Timeline 上下文缓存新映射，后续一致性检查生效

## 📌 总结：Reality–Fiction Bridge 的价值

传统做法 你的系统（有此上下文）
-------- ---------------------
作者脑中记住“亭城=滁州” 系统显式存储并推理
写错地点无法自动发现 自动检测“亭城 vs 南京”冲突
修改设定后需手动全局替换 映射变更自动影响所有关联事件
这个限界上下文，就是你所说的 “维护虚实之间桥梁” 的工程化实现。
