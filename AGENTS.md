# Thera - AI External Brain System

## Project Overview

Thera is an intelligent AI external brain system designed for macOS and developers. It provides an interactive CLI, large language model client wrapper (compatible with OpenAI-style APIs), and Graphiti knowledge graph integration to build an intelligent knowledge management and conversation system.

## Technology Stack

- **Language**: Python 3.10+ (currently using Python 3.13.9)
- **Package Manager**: UV (modern Python package manager)
- **Build System**: Hatchling
- **Knowledge Graph**: Graphiti with Neo4j backend
- **LLM Integration**: OpenAI-compatible API (supports DeepSeek, Qwen, and other models)
- **Configuration**: Pydantic Settings with environment variables

## Project Structure

```
src/thera/                 # Main package source
├── __main__.py           # CLI entry point
├── main.py               # Core Thera system class
├── cli.py                # Interactive CLI implementation
├── llm.py                # LLM client with Graphiti integration
├── config.py             # Configuration management
└── docs_importer.py      # Document import functionality

tests/                    # Unit tests
integrated_tests/         # Integration tests
examples/                 # Usage examples
scripts/                  # Development utilities
docs/                     # Documentation
dev_docs/                 # Development documentation (imported to KG)
```

## Core Architecture

### Main Components

1. **Thera Class** (`main.py`): Central orchestrator that manages LLM and knowledge graph interactions
   - Provides unified interface for chat, knowledge management, and intelligent conversations
   - Implements async context manager pattern for resource management
   - Key methods: `chat()`, `add_knowledge()`, `search_knowledge()`, `chat_with_knowledge()`

2. **LLM Clients** (`llm.py`): 
   - **DeepSeekClient**: OpenAI-compatible API wrapper with streaming support
   - **GraphitiClient**: Knowledge graph integration with Neo4j database

3. **Interactive CLI** (`cli.py`): Feature-rich command-line interface
   - Commands: chat, add, search, import_docs, list_docs, demo, info, version
   - Built on Python's `cmd` module with comprehensive help system

4. **Configuration** (`config.py`): Pydantic-based settings management
   - Loads from `.env` file with UTF-8 encoding
   - Type-safe configuration with validation

5. **Document Import** (`docs_importer.py`): Automated knowledge ingestion
   - Imports Markdown files into knowledge graph
   - Supports recursive directory scanning

## Build and Test Commands

### Development Setup
```bash
# Install dependencies with development mode
uv sync --dev

# Run tests
uv run pytest -v

# Run tests with coverage
uv run pytest --cov=thera --cov-report=term-missing

# Run the application
uv run thera
# or
python -m thera
```

### Configuration
1. Copy `.env.example` to `.env`
2. Configure required environment variables:
   - `LLM_API_KEY`, `LLM_BASE_URL`, `LLM_MODEL`
   - `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`, `NEO4J_DATABASE`

## Code Style Guidelines

### Development Rules
1. **Package Management**: Always use `uv` instead of `pip`
2. **CLI Development**: Add commands by creating `do_<command>` methods in `TheraCLI` class
3. **Async Usage**: Use async/await throughout for non-blocking operations
4. **Error Handling**: Include comprehensive exception handling with user-friendly messages
5. **Resource Management**: Use context managers for proper cleanup

### Architecture Patterns
- **Facade Pattern**: Tera class simplifies complex LLM and KG interactions
- **Context Manager Pattern**: Proper resource management with async context managers
- **Strategy Pattern**: Different clients implement different AI interaction strategies
- **Command Pattern**: CLI commands as separate methods

## Testing Instructions

### Test Structure
- **Unit Tests**: `/tests/` - Basic functionality testing with mocks
- **Integration Tests**: `/integrated_tests/` - Graphiti integration with real database
- **Test Files**: `test_cli.py`, `test_llm.py`, `test_graphiti.py`

### Running Tests
```bash
# All tests
uv run pytest -v

# Specific test file
uv run pytest tests/test_cli.py -v

# Integration tests
uv run pytest integrated_tests/ -v
```

## Security Considerations

1. **API Keys**: Store in `.env` file (already in `.gitignore`)
2. **Database Credentials**: Configure via environment variables
3. **No Hardcoded Secrets**: All credentials must be externalized
4. **Environment Isolation**: Use separate environments for development and production

## Key Features

1. **Interactive CLI**: Full-featured command-line interface with help, history, and completion
2. **Knowledge Graph Integration**: Automatic knowledge graph population from documents
3. **Document Import**: Batch import from directories with progress tracking
4. **Streaming Support**: Real-time streaming responses from LLM
5. **Async Support**: Full async/await support throughout the codebase
6. **Multi-Model Support**: Compatible with various OpenAI-style API providers

## Development Workflow

1. **Adding New CLI Commands**: Create `do_<command>` method in `TheraCLI` class
2. **Extending LLM Support**: Modify `DeepSeekClient` or add new client classes
3. **Knowledge Graph Operations**: Use `GraphitiClient` methods or extend functionality
4. **Configuration Changes**: Update `Settings` class in `config.py`

## Current Development Priority

- **TODO**: Design knowledge graph Episode creation methods (as noted in TODO.md)

## Usage Examples

### Basic Chat
```python
from thera import Thera

async with Thera() as thera:
    response = await thera.chat("Hello, how are you?")
    print(response)
```

### Knowledge-Enhanced Chat
```python
async with Thera() as thera:
    # Add knowledge
    await thera.add_knowledge("Python is a programming language")
    
    # Chat with knowledge context
    response = await thera.chat_with_knowledge("Tell me about Python")
    print(response)
```

### Interactive CLI
```bash
thera
# Then use commands: chat, add, search, import_docs, etc.
```

This project follows modern Python best practices with UV package management, comprehensive testing, and a modular architecture suitable for both individual developers and team collaboration scenarios.