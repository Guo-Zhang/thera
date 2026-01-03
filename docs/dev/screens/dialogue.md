# 对话页面

## 组件设计

```
DialogueScreen
└── Horizontal (主分栏容器)
    ├── Vertical (左侧区域：对话流 + 输入)
    │   ├── ScrollView (可滚动的对话历史)
    │   │   ├── Static (用户消息气泡 1)
    │   │   ├── Static (AI 消息气泡 1)
    │   │   ├── Static (用户消息气泡 2)
    │   │   └── Static (AI 消息气泡 2, ... etc.)
    │   └── Input (底部输入框，用于发送新消息)
    │
    └── Vertical (右侧区域：便签列表)
        ├── Static / Label (标题，如 "Saved Notes")
        └── ListView (或 ScrollView + Static 列表)
            ├── ListItem / Static (便签项 1: "会议纪要...")
            ├── ListItem / Static (便签项 2: "待办：修复 bug")
            ├── ListItem / Static (便签项 3: "灵感：TUI 教程")
            └── ... (动态追加)
```
