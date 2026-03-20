# Git 状态机

## 1. 概念定义

**Git 状态机**是对 quanttide-founder 项目中多仓库（主仓库 + 12 个子模块）协作状态的抽象模型。

- **状态**：仓库在任意时刻所处的业务状态（一致、同步、已提交...）
- **转移**：工具驱动状态从一个节点转移到另一个节点
- **约束**：非法转移被拒绝，确保仓库始终沿"安全轨道"流转

## 2. 主仓库状态

| 状态 | 标识 | 含义 | 允许的下一步 |
|------|------|------|--------------|
| Dirty | M0 | 有变更未提交 | doc-check |
| CleanAndConsistent | M1 | 干净且一致 | submodule-sync, 修改文件 |
| Inconsistent | M2 | 配置不一致 | 手动修复 |
| Synced | M3 | 子模块已同步 | auto-commit |
| Committed | M4 | 变更已提交 | git push |

### 状态流转图

```
M0 ──doc-check OK──► M1 ──submodule-sync──► M3 ──auto-commit──► M4
 │                       ▲                      │
 │                       │                      │
 └──doc-check FAIL──► M2                       │
         │                                        │
         └────────────手动修复────────────────────┘
         
M4 ──push OK──► M1
      │
      └──push FAIL──► E1 (Error)
```

## 3. 子模块状态

| 状态 | 标识 | 含义 |
|------|------|------|
| Behind | S0 | 落后远程 |
| UpToDate | S1 | 已同步 |
| Detached | S2 | 分离头指针 |

## 4. 错误状态

| 状态 | 标识 | 含义 | 处理方式 |
|------|------|------|----------|
| NetworkError | E1 | 网络问题 | 等待重试或人工介入 |
| ConsistencyError | E2 | 一致性失败 | 手动修复 YAML/.gitmodules |
| DetachedHeadError | E3 | 分离头指针 | checkout 到分支 |
| PermissionError | E4 | 权限不足 | 检查文件权限 |

## 5. 状态转移表

| 当前状态 | 事件 | 结果状态 | 说明 |
|----------|------|----------|------|
| M0 | doc_check_ok | M1 | 一致性检查通过 |
| M0 | doc_check_fail | M2 | 一致性检查失败 |
| M1 | submodule_sync | M3 | 子模块同步成功 |
| M1 | edit | M0 | 修改文件 |
| M2 | fix | M1 | 手动修复一致 |
| M3 | auto_commit | M4 | 提交并推送 |
| M4 | push_ok | M1 | 推送成功，回到干净 |
| M4 | push_fail | E1 | 推送失败，进入错误态 |

### 非法转移（需拒绝）

| 当前状态 | 禁止事件 | 原因 |
|----------|----------|------|
| M0 | submodule_sync | 需先通过 doc-check |
| M0 | auto_commit | 需先通过 doc-check |
| M2 | submodule_sync | 需先修复一致性 |
| M2 | auto_commit | 需先修复一致性 |

## 6. 工作流映射

| 工具 | 状态转移 | 业务意义 |
|------|----------|----------|
| doc-check | M0 → M1/M2 | "配置是否一致" |
| submodule-sync | M1 → M3 | "子模块是否同步" |
| auto-commit | M3 → M4 → M1 | "变更是否已记录" |

### 标准工作流

```
修改代码
    │
    ▼
doc-check      ──► 验证一致
    │                 │
    │ OK              │ FAIL
    ▼                 ▼
submodule-sync     手动修复
    │                 │
    ▼                 ▼
auto-commit        回到 doc-check
    │
    ▼
push ──OK──► 完成（M1）
      │
      FAIL
      │
      ▼
  错误处理（E1）
```

## 7. 与 Git 状态的关系

Git 本身的状态机（技术层面）：
- 文件：未跟踪 → 已修改 → 已暂存 → 已提交
- 命令：edit → add → commit → push

Thera 的状态机（业务层面）：
- 仓库：Dirty → Consistent → Synced → Committed → Synced
- 命令：edit → doc-check → submodule-sync → auto-commit

```
Git 状态机（技术）    封装/约束    Thera 状态机（业务）
─────────────────────────────────────────────────────
Modified/Staged/      ───────►    Consistent/Synced/
Committed                         Committed
```

## 8. 异常处理

| 场景 | 检测 | 处理 |
|------|------|------|
| 网络超时 | push 失败 | 等待重试，记录 E1 |
| 配置不一致 | doc-check 失败 | 拒绝继续，提示修复 |
| 分离头指针 | submodule status | 拒绝同步，提示修复 |
| 权限不足 | git 返回 128 | 拒绝操作，提示检查权限 |
