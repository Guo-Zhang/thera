# 默认活动：增量式被动观察

## 功能说明

实现"嵌入式批注"功能：AI 不负责全篇重写，只负责"扫描"和"打标"，在用户写作停顿时自动为段落添加观察者视角的结构化信息。

## 输入输出

- **输入**：原始工作日志（Markdown 格式）
- **输出**：带嵌入式批注的日志（保留原文，在段落末尾插入批注）

## 模块规划

### 1. 命令行入口

文件：`src/thera/cli.py`

```python
def main():
    parser = argparse.ArgumentParser(description='增量式被动观察')
    parser.add_argument('file', help='日志文件路径')
    args = parser.parse_args()
    
    # 加载配置
    config = load_config()
    
    from thera.mode.default import JournalProcessor
    processor = JournalProcessor(config)
    processor.process(args.file)
```

### 2. 核心处理器

文件：`src/thera/mode/default.py`

```python
class JournalProcessor:
    def __init__(self, config: Config):
        self.config = config
        self.llm = LLMClient(config)
    
    def process(self, file_path: str):
        content = read_file(file_path)
        paragraphs = split_paragraphs(content)
        new_content_parts = []
        
        for para in paragraphs:
            if is_already_annotated(para) or is_short(para):
                new_content_parts.append(para)
                continue
            
            annotation = self.llm.get_annotation(para)
            if annotation != "SKIP":
                updated_para = f"{para}\n\n{annotation}"
                new_content_parts.append(updated_para)
            else:
                new_content_parts.append(para)
        
        # 全量写回，保证原子性
        write_file(file_path, '\n\n'.join(new_content_parts))

### 3. LLM 客户端

文件：`src/thera/llm.py`

```python
class LLMClient:
    def __init__(self, config: Config):
        self.config = config
        self.opencode_path = config.opencode_path
    
    def get_annotation(self, text: str) -> str:
        # 调用 opencode 获取批注
        pass
```

### 4. 配置文件

文件：`src/thera/config.py`

```python
@dataclass
class Config:
    opencode_path: str = "/usr/local/bin/opencode"
    model: str = "o4-mini"
    max_retries: int = 3

def load_config() -> Config:
    """从 config.yaml 加载配置"""
    import yaml
    with open('config.yaml') as f:
        data = yaml.safe_load(f)
    return Config(**data)
```

## 处理逻辑

### 1. 段落切分
- 按 `\n\n`（空行）将全文切分为多个"逻辑段落"
- 过滤：忽略只有标点、代码块或过短（<20字）的段落
- 过滤：忽略空字符串段落（连续空行产生）

```python
def split_paragraphs(content: str) -> list[str]:
    paragraphs = content.split('\n\n')
    # 过滤空字符串和纯空白段落
    return [p.strip() for p in paragraphs if p.strip()]
```

### 2. 状态检测
- 检查每个段落是否已存在 `🤖 观察者注` 标记（注意：不加粗体，与 Prompt 输出保持一致）
- 已存在 → 跳过（保持幂等性）
- 不存在 → 标记为"待观察段落"

### 3. AI 提炼
- 针对每个待观察段落，AI 进行轻量级推理
- Prompt 策略：判断核心价值，若无意义闲聊则输出 SKIP，若包含洞察/决策/风险则按格式输出批注

### 4. 合成回写
- 将原文段落 + AI 生成的批注拼接
- 写回文件

## Prompt

### 系统 Prompt

```
你是一个安静的观察者。你的任务是为用户的工作日志添加结构化批注。
```

### 用户 Prompt

```
阅读以下段落，判断其核心价值。

段落内容：
{paragraph}

如果它只是无意义的闲聊或过渡语，请输出：SKIP

如果它包含洞察、决策或风险，请按以下格式输出批注（使用引用语法 >）：
> 🤖 观察者注
> 🏷️ 标签：<分类1> <分类2>
> 💎 提炼：<提取的标准化知识>
> ⚠️ 状态：<状态说明>
> 🔗 关联：<关联说明>
> 🔑 关键：<关键要点>
> 🔄 模式：<模式说明>

注意：
1. 只输出批注内容，不要修改原文
2. 标签使用 # 前缀
3. 提炼要简洁，不超过 50 字
4. 非必填项可省略
```

## 伪代码

```python
def process_journal(file_path):
    content = read_file(file_path)
    paragraphs = content.split('\n\n')
    new_content_parts = []
    
    for para in paragraphs:
        if is_already_annotated(para):
            new_content_parts.append(para)
            continue
        if len(para.strip()) < 20:
            new_content_parts.append(para)
            continue
        
        annotation = get_ai_annotation(para)
        if annotation != "SKIP":
            updated_para = f"{para}\n\n{annotation}"
            new_content_parts.append(updated_para)
        else:
            new_content_parts.append(para)
    
    write_file(file_path, '\n\n'.join(new_content_parts))

def is_already_annotated(text):
    return "🤖 观察者注" in text
```

## 格式规范

批注结构：
- 🏷️ 标签：对内容进行定性（如 #核心洞察、#待办、#工程决策）
- 💎 提炼：从口语中提取的标准化知识或命题
- 🔗 关联：识别到的潜在关联或冲突
- ⚠️ 状态：标注状态（如模糊阶段、暂不紧急）
- 🔑 关键：关键要点
- 🔄 模式：模式说明

## 触发机制

手动触发：在终端执行以下命令：

```bash
python -m thera.cli <file-path>
```

## 配置文件

文件：`config.yaml`

```yaml
opencode_path: /usr/local/bin/opencode
model: o4-mini
max_retries: 3
```

## 错误处理

- **opencode 获取异常**：处理 opencode 调用失败的情况，包括网络异常、响应解析错误等
- 重试机制：默认重试 3 次
- 跳过策略：异常段落记录日志后继续处理下一段

## 成本控制

使用 opencode 免费模型，暂无 Token 限制。

## 测试 Fixture

- 输入：`tests/fixtures/default/journal_2026-03-15_input.md`
- 输出：`tests/fixtures/default/journal_2026-03-15_output.md`

## 开发步骤

1. 创建 `src/thera/` 目录结构
2. 实现 `config.py` 配置类
3. 实现 `llm.py` OpenCode 客户端
4. 实现 `mode/default.py` 核心处理器
5. 实现 `cli.py` 命令行入口
6. 编写单元测试
7. 集成测试
