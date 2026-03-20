# Thera - 数字资产治理工具

## 1. 产品定位

**Thera** 是一套基于 Python 的命令行工具集，面向 quanttide-founder 项目（Monorepo + Git Submodules 架构），提供数字资产的一致性检查、同步管理和自动化提交功能。

## 2. 核心问题

| 问题 | 影响 |
|------|------|
| 主仓库与子模块版本不同步 | YAML 记录与实际代码状态脱节 |
| 人工 git 操作繁琐易错 | 容易漏掉子模块或忘记写日志 |
| 变更历史难以追溯 | 缺少标准化的提交和日志规范 |

## 3. 功能规格

### 3.1 工具矩阵

| 工具 | 命令 | 核心功能 |
|------|------|----------|
| **doc-check** | `doc-check [--config PATH] [--repo PATH]` | 验证 YAML 事实源与 .gitmodules 一致性 |
| **submodule-sync** | `submodule-sync [--check\|--sync PATHS\|--sync-all] [--repo PATH]` | 检测并拉取子模块远程更新 |
| **auto-commit** | `auto-commit [--dry-run] [--repo PATH]` | 检测变更，交互确认后按序提交推送 |

### 3.2 doc-check

**输入**：`meta/profile/submodules.yaml`

**检查项**：
1. YAML 中的 `name` 与 .gitmodules 中的 `path` 匹配
2. YAML 中声明的路径真实存在

**输出**：
- 检查通过：`[OK] N 个路径`
- 检查失败：`[FAIL] 缺失: path1, path2`

### 3.3 submodule-sync

**模式**：
- `--check`：检测远程更新，显示有更新的子模块
- `--sync PATHS`：同步指定子模块（逗号分隔）
- `--sync-all`：同步所有子模块

**实现**：使用 `git submodule update --remote --merge`

### 3.4 auto-commit

**工作流**：
```
检测变更 → 显示摘要 → 用户确认 → 按序提交推送（子模块 → 主仓库）→ 追加日志
```

**变更类型识别**：

| 类型前缀 | 检测路径 |
|----------|----------|
| `docs` | `docs/` |
| `code` | `src/` |
| `config` | `.gitmodules`, `.gitignore` |
| `meta` | `meta/` |
| `root` | 根目录其他文件 |

**提交消息格式**：
- 子模块：`[{type}] {files}`
- 主仓库：`[sync] [{type}] {files}, ...`

**日志格式**：
```markdown
- 17:30 OK main: [code] src/thera
- 17:30 FAIL src/thera: [code] src/thera/*.py
```

## 4. 标准工作流

```
修改代码/文档
    │
    ▼
┌─────────────────┐
│  doc-check      │ ──► 验证事实源与配置一致性
└─────────────────┘
    │
    ▼ (如有更新)
┌─────────────────┐
│ submodule-sync  │ ──► 同步子模块到最新
│   --sync-all    │
└─────────────────┘
    │
    ▼
┌─────────────────┐
│  auto-commit    │ ──► 提交并推送到云端
│                 │     追加日志到 journal
└─────────────────┘
```

## 5. 约束条件

| 条件 | 说明 |
|------|------|
| Python 版本 | >= 3.10 |
| 依赖 | 仅使用标准库（subprocess, pathlib, argparse） |
| 环境变量 | 需要设置 `PYTHONPATH=src/thera/src` |
| Git 配置 | 已启用 `submodule.recurse` |

## 6. 退出码约定

| 工具 | 0 | 1 |
|------|---|---|
| doc-check | 检查通过 | 有缺失 |
| submodule-sync | 无更新/成功 | 检测到更新/失败 |
| auto-commit | 全部成功 | 有失败 |

## 7. 技术实现

- **入口**：`src/thera/src/thera/cli.py`
- **子模块**：各自独立封装 `run_git()` 函数
- **调用方式**：`python3 src/thera/src/thera/cli.py <command>`
