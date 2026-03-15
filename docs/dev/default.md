# 默认活动：增量式被动观察

## 功能说明

实现"嵌入式批注"功能：AI 不负责全篇重写，只负责"扫描"和"打标"，在用户写作停顿时自动为段落添加观察者视角的结构化信息。

## 输入输出

- **输入**：原始工作日志（Markdown 格式）
- **输出**：带嵌入式批注的日志（保留原文，在段落末尾插入批注）

## 处理逻辑

### 1. 段落切分
- 按 `\n\n`（空行）将全文切分为多个"逻辑段落"
- 过滤：忽略只有标点、代码块或过短（<20字）的段落

### 2. 状态检测
- 检查每个段落末尾是否已存在 `> **🤖 观察者注**` 标记
- 已存在 → 跳过（保持幂等性）
- 不存在 → 标记为"待观察段落"

### 3. AI 提炼
- 针对每个待观察段落，AI 进行轻量级推理
- Prompt 策略：判断核心价值，若无意义闲聊则输出 SKIP，若包含洞察/决策/风险则按格式输出批注

### 4. 合成回写
- 将原文段落 + AI 生成的批注拼接
- 写回文件

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
    return "**🤖 观察者注**" in text
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
python agent.py design-log.md
```

## 配置文件

- **opencode 路径**：本地 opencode 可执行文件路径（需用户配置）

## 错误处理

- **opencode 获取异常**：处理 opencode 调用失败的情况，包括网络异常、响应解析错误等

## 成本控制

使用 opencode 免费模型，暂无 Token 限制。

## 模块规划

待定（需要进一步明确业务逻辑后确定模块划分）

## 测试 Fixture

- 输入：`tests/fixtures/default/journal_2026-03-15_input.md`
- 输出：`tests/fixtures/default/journal_2026-03-15_output.md`
