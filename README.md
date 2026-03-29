# thera

`thera` 是一个模块化 AI 外脑原型，面向 macOS 开发场景，提供：
- 多领域（Domain）对话与切换（think / write / knowl / connect）
- 本地数据存储与状态管理
- Apple Notes 导入与 memo 活动分析流水线
- 文档与运维审计脚本

## 环境要求

- Python `>=3.10, <3.14`
- 推荐使用 `uv`
- 如需使用知识/分析能力，需要配置 LLM 与 Neo4j 相关环境变量

## 快速开始

```bash
# 1) 安装依赖（含 GUI 支持）
uv sync --dev --extra gui

# 2) 配置环境变量
cp .env.example .env

# 3) 启动 TUI
uv run thera
```

## 环境变量

复制模板并配置：

```bash
cp .env.example .env
```

关键变量：
- `LLM_API_KEY`
- `LLM_BASE_URL`
- `LLM_MODEL`
- `LLM_EMBEDDING_MODEL`
- `LLM_RERANKER_MODEL`
- `NEO4J_URI`
- `NEO4J_USER`
- `NEO4J_PASSWORD`
- `NEO4J_DATABASE`

## 常用命令

```bash
# 查看版本
uv run thera --version

# 运行测试
uv run pytest -v

# 运行单测文件
uv run pytest tests/test_think_domain.py -v

# 覆盖率
uv run pytest --cov=thera --cov-report=term-missing
```

## 目录结构

```text
src/thera/
  __main__.py            # 程序入口（TUI + 参数解析）
  meta.py                # Domain 抽象与 DomainManager
  config.py              # 统一配置
  domain/                # 领域模块
    think.py
    write.py
    knowl.py
    connect.py
  infra/                 # 外部系统集成
    apple.py             # Apple Notes 导入
    feishu.py
    github.py
    llm.py
  activity/              # 活动流水线
    memo.py              # 备忘录分析
  state/
    storage_state.py     # 本地存储状态管理

docs/
  RAEDME.md              # 文档索引（文件名保持现状）
  dev/                   # 开发文档
  user/                  # 用户指南
  ops/                   # 运维与审计
```

## 最小工作流

### Apple Notes -> Memo 分析

```bash
# 导出“思考”文件夹备忘录到 data/infra/apple/notes.json
uv run python -c "from quanttide_apple import export_notes; from pathlib import Path; export_notes('思考', Path('data/infra/apple/notes.json'))"

# 执行 memo activity，输出到 data/activity/memo/
uv run python -c "from thera.activity.memo import run_memo_activity; run_memo_activity()"
```

### 知识库 -> 知识发现

```bash
# 克隆知识库到 data/infra/github/
git clone https://github.com/quanttide/quanttide-profile-of-founder data/infra/github

# 执行 profile activity，输出到 data/activity/profile/
uv run python -c "from thera.activity.profile import run_profile_activity; run_profile_activity()"
```
