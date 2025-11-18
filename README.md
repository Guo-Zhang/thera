# `thera`：苹果的AI外脑系统

智能 AI 外脑系统（面向 macOS / 开发者）。

主要功能：提供交互式 CLI、大模型客户端封装（兼容 OpenAI 风格接口），以及 Graphiti 知识图谱集成，构建智能知识管理与对话系统。

---

## 要求

- Python 3.10+
- Neo4j 数据库（用于知识图谱存储）
- OpenAI API 密钥或兼容 API 密钥
- 推荐使用虚拟环境（venv / pyenv / conda 等）

---

## 快速开始（开发者）

### 1. 环境准备

克隆仓库并进入项目目录：

```bash
git clone https://github.com/Guo-Zhang/thera.git
cd thera
```

创建并激活虚拟环境：

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
```

使用 uv 安装依赖：

```bash
uv sync --dev
```

### 2. 配置环境变量

创建 `.env` 文件（参考 `.env.example`）：

```bash
# 复制环境变量模板
cp .env.example .env
# 编辑 .env 文件，设置你的 API 密钥和数据库连接
```

### 3. 启动系统

运行交互式 CLI：

```bash
thera
```

查看版本：

```bash
thera --version
```

运行功能演示：

```bash
thera
# 在 CLI 中输入: demo
```

---

## 项目结构

```
.
├── pyproject.toml          # 项目及依赖配置
├── README.md               # 本文件
├── src/thera               # Python 包源码
│   ├── __init__.py
│   ├── __main__.py         # 主入口文件
│   ├── cli.py              # 交互式 CLI
│   ├── llm.py              # DeepSeek / OpenAI-兼容客户端，含 Graphiti 集成
│   ├── config.py           # 配置管理
│   └── main.py             # 主系统类 Thera
├── tests/                  # 单元测试
│   ├── test_cli.py
│   └── test_llm.py
├── examples/               # 示例代码
│   ├── graphiti.py         # Graphiti 示例
│   ├── llm.py              # 基础 LLM 示例
│   └── config.py           # 示例配置
└── .claude/                # Claude Code 配置
    └── commands/thera.md   # Thera 命令快捷方式
```

---

## 测试

使用 uv 运行测试：

```bash
# 运行所有测试
uv run pytest -v

# 查看测试覆盖率
uv run pytest --cov=thera --cov-report=term-missing
```

## 核心功能

### 智能对话
```python
from thera.main import Thera
import asyncio

async def example():
    async with Thera() as thera:
        # 结合知识图谱的智能对话
        response = await thera.chat_with_knowledge("Python 有哪些特性?")
        print(f"回答: {response['response']}")
        print(f"参考知识: {response['knowledge_references']}")

asyncio.run(example())
```

### 知识管理
```python
# 添加知识
thera.add_knowledge_sync("Python特性", "Python 是一种高级编程语言，具有简洁的语法和强大的标准库。")

# 搜索知识
results = thera.search_knowledge_sync("编程语言")
```

### 基础聊天
```python
client = DeepSeekClient()
response = client.generate("写一段关于机器学习的简介")
```

---

## 开发说明

### CLI 开发
- 添加 CLI 命令：在 `src/thera/cli.py` 的 `TheraCLI` 类中添加 `do_<命令名>` 方法即可自动成为新的交互命令。

### 核心模块说明
- `thera.main.Thera` - 主系统类，集成 LLM 和 Graphiti 功能
- `thera.llm.DeepSeekClient` - 兼容 OpenAI 接口的大模型客户端
- `thera.llm.GraphitiClient` - Graphiti 知识图谱客户端
- `thera.config.settings` - 配置管理

### 环境配置
创建一个 `.env` 文件，包含以下变量：
```bash
LLM_API_KEY=your_api_key
LLM_BASE_URL=https://api.siliconflow.cn/v1/
LLM_MODEL=deepseek-ai/DeepSeek-V3.1-Terminus
LLM_EMBEDDING_MODEL=Qwen/Qwen3-Embedding-8B
LLM_RERANKER_MODEL=Qwen/Qwen3-Reranker-8B
NEO4J_URI=neo4j://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
```

或直接复制模板：
```bash
cp .env.example .env
# 然后编辑 .env 文件填入真实值
```

### Claude Code 集成
项目已配置 Claude Code，可使用 `/thera` 快捷命令：
- `/thera chat <消息>` - 智能对话
- `/thera add <标题> <内容>` - 添加知识
- `/thera search <查询>` - 搜索知识图谱

### 文档导入
项目提供文档导入功能，可将文档内容自动导入到知识图谱：

#### CLI 交互模式
```bash
thera
# 在 CLI 中执行:
import_docs                # 导入 dev_docs 目录
import_docs /path/to/docs  # 导入指定目录
list_docs                  # 列出已导入文档
```

#### 独立脚本
```bash
# 使用独立脚本导入
dev_docs.py
```

#### 编程方式
```python
from thera.docs_importer import DocsImporter
import asyncio

async def import_docs():
    async with DocsImporter() as importer:
        await importer.import_dev_docs()  # 导入 dev_docs

asyncio.run(import_docs())
```

---

## 贡献

欢迎 PR、Issue 与讨论。贡献时请遵守以下建议：

- 每个新功能附带测试。
- 在本地运行测试并通过：`uv run pytest`。
- 保持提交信息清晰。

---

## 许可证

见仓库根目录的 `LICENSE` 文件。

```

