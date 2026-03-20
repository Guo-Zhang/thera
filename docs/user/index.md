# Thera 工具索引

## 概述

Thera 提供三个命令行工具，服务于 quanttide-founder 的数字资产治理：

```text
┌─────────────────────────────────────────────────────────────────────┐
│                     数字资产治理工作流                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│   ┌──────────┐     ┌──────────┐     ┌──────────┐                   │
│   │ doc-check │ ──► │submodule │ ──► │auto-commit│                  │
│   │   检查   │     │  _sync   │     │   提交   │                   │
│   │ 一致性   │     │   同步   │     │  推送    │                   │
│   └──────────┘     └──────────┘     └──────────┘                   │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## 工具对照

| 工具 | 命令 | 用途 |
|------|------|------|
| [doc-check](./doc-check.md) | `doc-check` | 验证 YAML 与 .gitmodules 一致性 |
| [submodule-sync](./submodule-sync.md) | `submodule-sync` | 拉取子模块远程更新 |
| [auto-commit](./auto-commit.md) | `auto-commit` | 检测变更并提交推送 |

## 标准工作流

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

## 典型场景

### 场景一：日常开发

```bash
# 1. 修改代码后，先检查一致性
python3 src/thera/src/thera/cli.py doc-check

# 2. 提交并推送
python3 src/thera/src/thera/cli.py auto-commit
```

### 场景二：同步他人更新

```bash
# 1. 检查远程更新
python3 src/thera/src/thera/cli.py submodule-sync --check

# 2. 如有更新，同步所有子模块
python3 src/thera/src/thera/cli.py submodule-sync --sync-all

# 3. 检查一致性
python3 src/thera/src/thera/cli.py doc-check

# 4. 提交主仓库指针变更
python3 src/thera/src/thera/cli.py auto-commit
```

### 场景三：审查准备

```bash
# 仅检查一致性
python3 src/thera/src/thera/cli.py doc-check
```

## 环境准备

```bash
# 设置 PYTHONPATH（每个会话只需一次）
export PYTHONPATH=src/thera/src

# 查看帮助
python3 src/thera/src/thera/cli.py --help
```
