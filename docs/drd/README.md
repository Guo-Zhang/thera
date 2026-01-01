# 交互设计文档

## 页面

### 智能备忘页面

```
MemoScreen
├── MemoPanel
│   ├── MemoContext    ← 当前备忘的沟通语境
│   └── Memo           ← 备忘正文内容
└── MessagePanel
    ├── MessageContext ← 当前对话的沟通语境
    ├── MessageList    ← 原始对话消息流
    └── InputBar       ← 用户输入区
```
