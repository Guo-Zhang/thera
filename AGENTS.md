# CODEBUDDY.md

This file provides guidance to CodeBuddy Code when working with code in this repository.

## Common Commands

```bash
# Install dependencies (development mode)
uv sync --dev

# Run all tests
uv run pytest -v

# Run a single test file
uv run pytest tests/test_cli.py -v

# Run a single test function
uv run pytest tests/test_cli.py::test_function_name -v

# Run tests with coverage
uv run pytest --cov=thera --cov-report=term-missing

# Run the CLI application
uv run thera

# Or use python directly
python -m thera

# Check version
thera --version
```

## Environment Setup

Copy `.env.example` to `.env` and configure:
- `LLM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL`
- `LLM_EMBEDDING_MODEL`, `LLM_RERANKER_MODEL`
- `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`, `NEO4J_DATABASE`

## Project Architecture

This is a **modular AI knowledge management system** with multiple independent components:

### 1. Knowledge Graph Module (`examples/knowl/`)
- **graphiti.py**: Graphiti client integration with Neo4j for episodic memory
- **neo4j_graphrag.py**: Neo4j native RAG implementation using `neo4j-graphrag` library
- **config.py**: Shared Pydantic Settings for knowledge modules

Key classes:
- `Graphiti` (from `graphiti_core`): Episodic knowledge graph with temporal reasoning
- `VectorRetriever`, `GraphRAG` (from `neo4j-graphrag`): Vector-based retrieval

### 2. Connect Module (`examples/connect/`)
- **models/context.py**: Context management with authority sources (SYSTEM, USER, NEGOTIATED) and confirmation status (PENDING, CONFIRMED, DISPUTED)
- **models/dialogue.py**: Dialogue history management
- **views/**: UI components for displaying messages and memos
- **screens/**: Full screen implementations (e.g., dialogue screen)

### 3. Write Module (`examples/write/`)
- **analyzer.py**: Novel fragment organization analyzer
  - `FragmentAnalyzer`: Analyzes how story fragments integrate into main text
  - `Dialogue`: Speaker inference (male/female/other/unknown), validity detection
  - `DocumentInfo`: Title, word count, paragraphs, dialogues, emotional tone
  - Features: keyword extraction, location detection, emotional analysis, similarity scoring

### 4. Docs Module (`examples/docs/`)
- **feishu.py**: Lark (Feishu) API integration for document processing
- **feishu_to_jupyterbook.py**: Convert Feishu documents to JupyterBook format

### 5. Core Package (`src/thera/`)
Currently minimal - package entry points only. Main logic lives in examples.

## Data Storage

- `data/`: Runtime data (jupyterbook content, analysis outputs)
- `docs/`: Imported documentation organized by category
- `dev_docs/`: Development documentation (imported to knowledge graph)

## Key Dependencies

- `graphiti-core`: Knowledge graph with episodic memory
- `neo4j-graphrag`: Neo4j RAG implementation
- `openai`: OpenAI-compatible API client
- `pydantic-settings`: Configuration management
- `textual`: TUI framework
- `lark-oapi`: Feishu/Lark API client

## Data Safety Rules

1. **删除前确认** - 涉及用户数据的操作（移动、删除、重命名），必须先询问用户确认
2. **不主动删除** - 避免使用 `rm -rf` 等破坏性命令，优先用 safe delete 或先检查
3. **操作前备份** - 重要数据操作前，先检查是否存在，必要时备份
4. **读取为主** - 优先读取用户数据而非修改，修改前确认
