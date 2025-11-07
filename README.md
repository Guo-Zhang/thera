# thera

轻量级 AI 外脑示例工具包（面向 macOS / 开发者）。

主要目标：提供一个小型交互式 CLI、示例的大模型客户端封装（兼容 OpenAI 风格接口），以及可运行的测试示例，便于学习与扩展。

---

## 要求

- Python 3.14+
- 推荐使用虚拟环境（venv / pyenv / conda 等）

---

## 快速开始（开发者）

克隆仓库并进入项目目录：

```bash
git clone https://github.com/Guo-Zhang/thera.git
cd thera
```

创建并激活虚拟环境（macOS / Linux 示例）：

```bash
python -m venv .venv
source .venv/bin/activate
```

安装项目（可编辑模式，便于开发）：

```bash
pip install -e .
```

运行交互式 CLI：

```bash
thera
```

查看版本：

```bash
thera --version
```

---

## 项目结构

```
.
├── pyproject.toml       # 项目及依赖配置
├── README.md            # 本文件
├── src/thera            # Python 包源码
│   ├── __init__.py
   ├── __main__.py
   ├── cli.py           # 交互式 CLI
   └── llm.py           # DeepSeek / OpenAI-兼容客户端封装示例
└── tests/               # 单元测试
	├── test_cli.py
	└── test_llm.py
```

---

## 测试（使用 uv + pytest）

本仓库示例使用 `pytest` 作为主要测试工具，并在 README 中统一使用 `uv run` 作为命令前缀以适配使用 `uv` 的工作流（如果你没有 `uv`，也可以直接运行同样的命令，例如 `pytest` 或 `python -m unittest`）。

1. 安装测试依赖：

```bash
pip install -e ".[test]"
```

2. 使用 `uv` 运行 pytest：

```bash
uv run pytest -v
```

3. 查看覆盖率（pytest-cov）：

```bash
uv run pytest --cov=thera --cov-report=term-missing
```

4. （可选）运行基于标准库 unittest 的发现器：

```bash
uv run python -m unittest discover -v
```

注：`uv run` 是一个通用的命令包装前缀，用于在某些环境中确保命令在正确的虚拟环境或容器上下文中执行。如果你的系统没有 `uv`，直接运行后面的命令同样有效。

---

## 开发说明

- 添加 CLI 命令：在 `src/thera/cli.py` 的 `TheraCLI` 类中添加 `do_<命令名>` 方法即可自动成为新的交互命令。
- 大模型客户端示例：`src/thera/llm.py` 中包含 `DeepSeekClient`，它封装了对 OpenAI 兼容接口（例如 DeepSeek）的基本调用逻辑。真实调用时请设置 `OPENAI_API_KEY` 环境变量或在构造时传入 `api_key`。

示例：

```python
from thera.llm import DeepSeekClient

client = DeepSeekClient(api_key="<your-key>")
print(client.generate("写一段关于测试驱动开发的简介。"))
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

