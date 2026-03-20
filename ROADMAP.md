# Thera Roadmap

## 概述

本文档记录 Thera 的演进规划和探索方向。

## 核心状态模型

### 主仓库状态

| 状态 | 标识 | 含义 |
|------|------|------|
| Dirty | M0 | 有变更未提交 |
| CleanAndConsistent | M1 | 干净且一致 |
| Inconsistent | M2 | 配置不一致 |
| Synced | M3 | 子模块已同步 |
| Committed | M4 | 变更已提交 |

### 子模块状态

| 状态 | 标识 | 含义 |
|------|------|------|
| Behind | S0 | 落后远程 |
| UpToDate | S1 | 已同步 |
| Detached | S2 | 分离头指针 |

### 错误状态

| 状态 | 标识 | 含义 |
|------|------|------|
| NetworkError | E1 | 网络问题 |
| ConsistencyError | E2 | 一致性检查失败 |
| DetachedHeadError | E3 | 分离头指针 |
| PermissionError | E4 | 权限不足 |

## 版本规划

### v0.1.x - 基础工具集（当前）

- [x] doc-check：YAML 与 .gitmodules 一致性检查
- [x] submodule-sync：子模块远程同步
- [x] auto-commit：自动提交推送

### v0.2.x - CLI 统一入口

- [x] 统一 CLI 入口（cli.py）
- [x] 用户文档（docs/user/）
- [x] PRD 文档（docs/prd/）

### v0.3.x - 架构优化

- [ ] **抽取 git_ops.py**：统一封装所有 git 操作，消除重复 `run_git()` 代码
- [ ] **状态机核心**：显式追踪仓库状态（M0-M4），验证转移合法性
- [ ] **强制工作流顺序**：不允许跳过 doc-check 直接 auto-commit
- [ ] **显式错误分类**：E1-E4 错误状态

### v1.0.x - 稳定版

- [ ] 状态机重构完成
- [ ] 单元测试覆盖
- [ ] 集成测试覆盖

## 重构计划

### 目标

将分散在 CLI 中的状态判断逻辑，重构为显式的、集中的状态机管理模块。

### 好处

- **代码即模型**：代码结构与业务状态模型一致
- **健壮性**：状态机框架保证"非法状态不可达"
- **可测试性**：状态机逻辑独立于 CLI 单元测试

### 目标架构

```
cli.py → 状态机核心 (fsm.py) → Git 操作层 (git_ops.py)
```

### 模块职责

| 模块 | 职责 |
|------|------|
| `git_ops.py` | 封装所有 git 操作，统一 `run_git()`，返回明确结果 |
| `fsm.py` | 定义状态、合法转移事件、转移条件与回调 |
| `cli.py` | 解析命令，调用 git_ops 获取状态，触发 fsm 转移 |

### 迁移步骤

1. **抽取**：创建 `git_ops.py`，迁移 `run_git()` 等函数
2. **并行**：保持原 CLI 不变，新建命令使用状态机
3. **切换**：确认无误后切换主入口
4. **增强**：钩子、并行处理、监控

## 状态转移表

| 当前状态 | 命令 | 转移后 |
|----------|------|--------|
| M0 | doc-check OK | M1 |
| M0 | doc-check FAIL | M2 |
| M2 | 修复 + doc-check OK | M1 |
| M1 | submodule-sync --sync-all | M3 |
| M3 | auto-commit | M4 |
| M4 | git push OK | M1 |
| M4 | git push FAIL | Error |
