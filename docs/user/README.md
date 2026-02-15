# Thera 用户指南

## 启动

```bash
thera --mode chat
```

## 领域

Thera 支持多个领域（Domain），可通过命令切换：

| 命令 | 功能 |
|------|------|
| `/chat` | 对话域 - AI 聊天 |
| `/think` | 思考域 - 想法管理 |
| `/write` | 写作域 - 小说创作 |
| `/knowl` | 知识域 - 知识发现 |
| `/connect` | 连接域 - 便签管理 |

## 思考域

### 保存想法

```bash
/idea 今天天气真好
/idea [life] 去超市买菜
/idea [work] 项目启动
```

格式：`/idea [分类] 内容`

- 自动分类：根据关键词识别为 work/life
- 手动分类：用 `[life]` 或 `[work]` 指定

### 头脑风暴

```bash
/brainstorm AI 产品设计
```

## 知识域

### 知识发现

```bash
/discover
```

分析 `~/thera/docs/fiction` 目录下的文档，生成相似度报告和知识发现报告。

## 存储

默认路径：`~/thera/`

```
~/thera/
├── knowl/           # 知识发现输出
├── think/          # 思考域数据
├── docs/           # 文档
└── write/         # 写作数据
```
