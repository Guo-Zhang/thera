# 用户指南

## 启动

```bash
uv run thera
# 或
python -m thera
```

## 启动参数

```bash
# 指定初始命令启动
uv run thera --command /think

# 指定数据目录
uv run thera --storage /path/to/thera-data
```

可用命令：`/think`、`/write`、`/knowl`、`/connect`、`/default`。

## 功能文档

- [默认活动](default.md)：增量式被动观察，为工作日志添加 AI 批注

## 交互示例

在 TUI 输入框中直接输入文本；使用斜杠命令可触发特定行为。

```text
/idea 完成项目复盘
/idea [work] 准备季度计划
/brainstorm 新产品方向
/connect 今天与客户确认了需求范围
```

## 数据位置

默认数据目录：`~/thera`

常见文件：
- 思考记录：`~/thera/think/ideas.json`
- 运行输出：项目目录下 `data/`

## 常见问题

- 启动时报配置错误：检查 `.env` 是否已创建且关键变量已填写
- 知识/分析能力不可用：检查 `LLM_*` 和 `NEO4J_*` 配置
