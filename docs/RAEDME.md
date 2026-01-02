# 工作文档

MVP目标：AI增强备忘录+语境摘要
技术栈： Python+Textual

流程：先对话、再落笔
1. 对话
2. 识别对话语境
3. 记录
4. 识别备忘语境

## 数据

个人category：
- 小说：杭城言情，etc
- 编程：AI 外脑

## 算法

算法思想：把深度思考放在“协作”的中心，用“慢思考”代替“快思考”。

实现方式：使用语境代替对话历史的回复：
1. 语境更新算法
2. 对话回复算法

state2 = f(state1, human message)
AI message = g(state2, human message)
