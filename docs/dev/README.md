# 开发者文档

## 目标

记录 thera 的架构设计、模块实现、开发约束与经验沉淀。

## 架构概览

| 项目 | 职责 | 技术栈 |
|------|------|--------|
| **thera** | 处理程序、生成 data | Python CLI |
| **studio** | 使用 data、交互展示 | Flutter |

**数据流：** `thera (生成) → data/ → studio (消费)`

## 开发命令

### thera

```bash
# 安装依赖
uv sync --dev

# 运行所有测试
uv run pytest -v

# 运行特定测试
uv run pytest tests/test_think_mode.py -v

# 运行审计脚本
uv run python scripts/audit.py
```

### studio

```bash
# 启动 Flutter 应用
./scripts/run-studio.sh

# 指定设备 (macos/chrome)
./scripts/run-studio.sh chrome

# 代码分析
cd src/studio && flutter analyze
```

## 核心模块

- 入口：`src/thera/__main__.py`
- 元模型：`src/thera/meta.py`
- Mode：`src/thera/mode/`
- Handlers：`src/thera/handlers/`
- Infra：`src/thera/infra/`
- Workspace：`examples/default/workspace/`

## 文档入口

- 工作区模块：`docs/dev/workspace/`
- 基础设施模块：`docs/dev/infra/`
- Mode 设计：`docs/dev/mode/`
- 元模型说明：`docs/dev/meta.md`
- 主流程说明：`docs/dev/main.md`

## 维护约定

- 新增/重构模块后，补充对应 `docs/dev/` 文档
- 文档记录实现逻辑与经验，不记录一次性运行输出
- 输出报告放到 `data/workspace/<module>/` 或 `docs/ops/reports/`

## 参考项目

### quanttide-profile-of-founder

项目地址：https://github.com/quanttide/quanttide-profile-of-founder

**可借鉴经验：**

| 维度 | 项目实践 | 适用场景 |
|------|----------|----------|
| 目录命名 | 使用小写字母、复数形式（如 `think/`、`write/`） | 知识库/文档项目 |
| 文件命名 | 小写字母、连字符分隔（如 `agent.md`） | 统一风格 |
| 板块划分 | 按主题领域划分目录（think/agent/knowl/learn/stdn/write/code/brand/acad/product） | 知识分类 |
| Markdown 规范 | ATX 标题、fenced code、列表使用 `-` 或 `1.` | 文档质量 |
| 质量检查 | markdownlint 验证 + 链接/YAML 语法检查 | CI/CD |

**与 thera 的对应关系：**

- 该项目的板块（think/、write/、knowl/）对应 thera 的 Mode 模块
- 该项目使用 Jupyter Book 构建，thera 可考虑类似的知识展示方案
