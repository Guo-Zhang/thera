# 文档工程模块

**项目目标**：构建一个稳健的飞书至 JupyterBook 的单向同步系统，建立以 JupyterBook (MyST Markdown) 为标准的统一知识结构。
#### 第一阶段：地基重构 —— 元数据锚定与 ID 持久化
**解决痛点**：文件名变动导致构建失败、版本追溯丢失。
1.  **文件命名规范重构**
    *   **废除**：使用 `title` 作为文件名（易冲突、易变更）。
    *   **确立**：使用 `node_token` 作为唯一文件标识符。
    *   **实施**：
        *   修改 `save_document_content`，输出文件名改为 `{node_token}.md`。
        *   建立 `manifest.json` 索引文件，存储 `node_token` <-> `title` <-> `file_path` 的映射关系。
2.  **YAML Front Matter 注入**
    *   **目标**：将飞书文档的隐性属性转化为 JupyterBook 的显性元数据。
    *   **实施**：
        *   编写 `generate_front_matter(block)` 函数。
        *   在每个 Markdown 文件头部注入：
            ```yaml
            ---
            title: "原始飞书标题"
            feishu_node_token: "doxcnxxxxx"
            feishu_obj_token: "xxxxx"
            feishu_url: "https://feishu.cn/..."
            created_at: "2023-10-01"
            updated_at: "2023-10-27"
            ---
            ```
#### 第二阶段：血脉疏通 —— 资源本地化与引用替换
**解决痛点**：图片裂链、文档无法离线阅读。
1.  **资源管理器**
    *   **目标**：剥离飞书托管，实现静态资源本地化。
    *   **实施**：
        *   创建 `AssetManager` 类。
        *   在 `feishu_dir` 下建立 `images/` 目录。
        *   编写图片下载逻辑，处理飞书临时链接（需带 Token 请求）。
2.  **链接重写机制**
    *   **目标**：确保 JupyterBook 构建时能找到本地图片。
    *   **实施**：
        *   在转换过程中解析图片 URL。
        *   下载图片并生成 hash 文件名（防止重名）。
        *   将 Markdown 中的 `![](https://...)` 替换为 `![](../images/hash_image.png)`。
#### 第三阶段：语义对齐 —— MyST 指令适配
**解决痛点**：排版丢失、富文本退化。
1.  **Block 映射表升级**
    *   **废除**：简单的字符串拼接（`**bold**`, `> quote`）。
    *   **确立**：输出符合 MyST 规范的指令。
    *   **实施**：
        *   **高亮块**：映射为 `{admonition}` 指令。
            ```markdown
            ```{note} 标题
            内容
            ```
            ```
        *   **代码块**：提取飞书的 `language` 字段，输出 ``` ```python。
        *   **表格**：解析飞书 `table` 属性，转换为 Markdown Table（需处理合并单元格的降级逻辑）。
2.  **内部链接修复**
    *   **目标**：修复飞书文档间的超链接。
    *   **实施**：
        *   解析 `[text](https://feishu.cn/docx/xxxxxx)` 链接。
        *   利用第一阶段生成的 `manifest.json`，将飞书链接替换为 JupyterBook 的内部相对路径引用。
#### 第四阶段：结构生成 —— 目录树与配置
**解决痛点**：手动维护 `_toc.yml` 繁琐易错。
1.  **自动化 TOC 生成**
    *   **实施**：
        *   读取飞书的 `feishu_wiki_directory.json` 树状结构。
        *   结合 `manifest.json` 定位文件。
        *   自动生成 JupyterBook 标准的 `_toc.yml` 文件，保留层级的父子关系。
#### 交付物清单
1.  **`converter.py`**：核心转换引擎（包含 AST 解析与 MyST 渲染）。
2.  **`downloader.py`**：处理图片、附件的下载与本地化。
3.  **`manifest.json`**：知识库索引数据库（核心中枢）。
4.  **`_toc.yml`**：JupyterBook 目录配置文件。
5.  **`markdown/`**：输出的 `.md` 文件夹（含元数据头）。
6.  **`images/`**：本地化的静态资源文件夹。
---
### 行动建议
**请立即执行第一阶段（Step 1.2 YAML Front Matter 注入）**。
这是投入产出比最高的一步。一旦每个文档都有了“身份证”和“档案”，后续无论是做搜索、做版本对比、还是做链接跳转，都有了数据基础。
这标志着你的代码正式从“文本处理脚本”升级为了“知识工程系统”。
