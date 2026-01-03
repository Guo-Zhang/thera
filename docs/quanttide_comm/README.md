# 沟通管理

## 领域模型

- 沟通主体：我、AI
- 沟通关系：上下级等。
- 沟通渠道：人机、私聊、群聊等。
- 沟通内容：xxxx
- 沟通语境：小说创作、产品研发等
- 沟通媒介：消息、便签、备忘
- 沟通范式：对话、画布
- 沟通反馈：YES or No

### 沟通内容

- 文本`Text`

### 沟通语境

语境（Context）是意义的生成机制（meaning-making framework）——它决定了同一段文字在不同情境下是讽刺、恳求、策略还是告别。
领域隐性框架（如小说创作、产品研发）

### 沟通反馈	

YES / NO（验证信息是否被有效理解或可用）

### 沟通媒介

Message（瞬时信号）、Note（临时捕捉）、Memo（结构输出）

- 消息`Message`
- 便签`Note`
- 备忘`Memo`

### 沟通模式

一个模式是对话模式，通过 Note 记录碎片，默认为单次 context 更新。
一个模式是画布模式，用来加工 Note 为 memo，默认为完整 context。

- 会话`Dialogue`
- 画布`Canvas`


## 界限上下文

Message -> Dialogue -> Note -> Canvas -> Memo

Context 是内置的抽象概念，并不参与交互。交互的是展示 Context 的 Note 或者 Memo。

