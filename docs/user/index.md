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
| `workflow status` | 查看当前状态 | 查看仓库状态和允许操作 |
| `workflow history` | 查看状态历史 | 查看状态转移记录 |
| `workflow audit` | 审计报告 | 生成审计统计报告 |

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
cd src/thera
source .venv/bin/activate

# 1. 修改代码后，先检查一致性
python src/thera/cli.py doc-check

# 2. 提交并推送
python src/thera/cli.py auto-commit
```

### 场景二：同步他人更新

```bash
cd src/thera
source .venv/bin/activate

# 1. 检查远程更新
python src/thera/cli.py submodule-sync --check

# 2. 如有更新，同步所有子模块
python src/thera/cli.py submodule-sync --sync-all

# 3. 检查一致性
python src/thera/cli.py doc-check

# 4. 提交主仓库指针变更
python src/thera/cli.py auto-commit
```

### 场景三：审查准备

```bash
cd src/thera
source .venv/bin/activate

# 仅检查一致性
python src/thera/cli.py doc-check
```

## 环境准备

```bash
cd src/thera
source .venv/bin/activate

# 查看帮助
python src/thera/cli.py --help
```

## 技术架构

Thera 采用三层架构设计：

```text
┌─────────────────────────────────────────┐
│  CLI 层 (cli.py)                        │ 用户交互入口
├─────────────────────────────────────────┤
│  Workflow 层 (workflow.py)              │ 状态管理、流程编排
├─────────────────────────────────────────┤
│  GitOps 层 (git_ops.py)                │ Git 操作封装
├─────────────────────────────────────────┤
│  FSM 层 (fsm.py)                       │ 状态机核心
└─────────────────────────────────────────┘
```

**状态机状态转移**：

```
DIRTY ──[doc_check_ok]──► CLEAN_AND_CONSISTENT
                              │
                              ▼ [submodule_sync]
                            SYNCED
                              │
                              ▼ [auto_commit]
                          COMMITTED ──[push_ok]──► CLEAN_AND_CONSISTENT
                              │
                              ▼ [push_fail]
                         NETWORK_ERROR
```

**特性**：

- 状态机确保操作的安全性
- 事务性工作流支持回滚
- 状态钩子支持自定义扩展
