# 元模块

系统观察与自省模块，用于描述系统自身的状态和属性。

## 当前架构

简化的命令路由架构：

```
Thera (入口)
  └── handlers (命令处理器)
      ├── /think → think.handle()
      ├── /write → write.handle()
      ├── /knowl → knowl.handle()
      └── /connect → connect.handle()
```

## 核心组件

### SystemState

系统状态快照，记录运行时信息：
- `started_at`: 启动时间
- `command_count`: 命令计数
- `uptime_seconds`: 运行时间

### get_system_info()

返回系统基本信息：
- `name`: "thera"
- `version`: "0.1.0"
- `description`: "AI Assistant"

## 与旧架构的差异

| 旧架构 | 新架构 |
|--------|--------|
| Domain (类) | Handler (函数) |
| DomainManager | 命令路由 |
| auto_switch | 显式命令前缀 |

旧架构过于复杂，已简化为命令分发模式。
