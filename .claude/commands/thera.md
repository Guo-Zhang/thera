# /thera - Thera AI Assistant Commands

Usage: `/thera [command]` or just `/thera` for help

Available commands:
- `/thera chat <message>` - Chat with Thera AI
- `/thera add <title> <content>` - Add knowledge to the graph
- `/thera search <query>` - Search the knowledge graph
- `/thera demo` - Run the demo
- `/thera info` - Show system information

## Examples

```bash
# Chat with Thera
/thera chat "什么是深度学习?"

# Add knowledge
/thera add "Python特性" "Python是一种高级编程语言，具有简洁的语法和强大的标准库。"

# Search knowledge
/thera search "编程语言"
```

## Configuration

Make sure your `.env` file is properly configured with:
- LLM_API_KEY
- LLM_BASE_URL
- LLM_MODEL
- NEO4J_URI
- NEO4J_USER
- NEO4J_PASSWORD