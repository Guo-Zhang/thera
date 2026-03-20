# 用户功能设计文档

**日期**: 2026-03-20
**范围**: workflow status / history / audit / strategy

---

## 概述

基于三层架构开发的用户功能，提供状态可视化、策略控制、审计报告能力。

## 功能列表

| 命令 | 功能 | 优先级 |
|------|------|--------|
| `workflow status` | 查看当前状态 | P0 |
| `workflow history` | 查看状态历史 | P1 |
| `workflow audit` | 审计报告 | P2 |
| `--strategy` | 收敛策略切换 | P1 |

---

## workflow status

### 功能说明

显示当前仓库状态和允许的操作。

### 命令行接口

```bash
thera workflow status [--repo PATH]
```

### 输出格式

```
当前状态: DIRTY
─────────────────────────────────────
变更: 3 个文件待提交

允许操作:
  • doc-check
─────────────────────────────────────
```

### 状态显示

| 状态 | 颜色 | 说明 |
|------|------|------|
| DIRTY | 红色 | 有变更未提交 |
| CLEAN_AND_CONSISTENT | 绿色 | 干净且一致 |
| INCONSISTENT | 黄色 | 配置不一致 |
| SYNCED | 蓝色 | 子模块已同步 |
| COMMITTED | 绿色 | 变更已提交 |
| *ERROR | 红色 | 错误状态 |

### 错误状态详情

```
当前状态: NETWORK_ERROR
─────────────────────────────────────
错误: 网络问题导致推送失败

最近一次推送:
  时间: 10:30:45
  提交: abc1234
  错误: connection timeout

建议操作:
  • 检查网络连接
  • 重试推送 (thera auto-commit)
─────────────────────────────────────
```

---

## workflow history

### 功能说明

显示状态机历史记录。

### 命令行接口

```bash
thera workflow history [--limit N] [--repo PATH]
```

### 输出格式

```
状态历史 (最近 10 条)
─────────────────────────────────────
10:40  DIRTY          → CLEAN_AND_CONSISTENT  [doc-check]
10:35  CLEAN_AND...   → SYNCED               [submodule-sync]
10:30  SYNCED         → COMMITTED             [auto-commit]
10:28  COMMITTED      → DIRTY                 [edit]
09:15  COMMITTED      → CLEAN_AND_CONSISTENT  [push]
─────────────────────────────────────
总计: 47 次状态转移
```

### 历史记录格式

```
{HH:MM}  {from_state:<15} → {to_state:<20} [{event}]
```

---

## workflow audit

### 功能说明

生成审计报告，包括错误统计、状态分布、操作频率。

### 命令行接口

```bash
thera workflow audit [--since DATE] [--until DATE] [--repo PATH]
```

### 输出格式

```
审计报告 (2024-01-01 至 2024-03-20)
================================================================================
概览
─────────────────────────────────────
状态转移: 47 次
错误次数: 2 次
平均停留时间: 2.3 分钟

状态分布
─────────────────────────────────────
DIRTY                  ████████████████████ 60%
CLEAN_AND_CONSISTENT  ██████████          30%
SYNCED                ██                   6%
COMMITTED             █                     3%
ERROR                 ▏                    1%

错误详情
─────────────────────────────────────
• 10:30 NETWORK_ERROR - push failed
  持续时间: 5 分钟
  恢复方式: 重试成功

• 14:22 CONSISTENCY_ERROR - doc check failed
  持续时间: 15 分钟
  恢复方式: 手动修复后恢复
================================================================================
```

### 统计数据

| 指标 | 说明 |
|------|------|
| 状态转移总数 | 历史记录中的转移次数 |
| 错误次数 | 进入 ERROR 状态的次数 |
| 平均停留时间 | 每个状态的平均持续时间 |
| 状态分布 | 各状态的时间占比 |

---

## --strategy 收敛策略

### 功能说明

控制子模块同步的收敛行为。

### 命令行接口

```bash
thera --strategy={auto|manual|hybrid}
thera submodule-sync --strategy={auto|manual|hybrid}
```

### 策略说明

| 策略 | 行为 | 适用场景 |
|------|------|----------|
| `auto` | 总是自动同步 | 信任子模块，可自动化 |
| `manual` | 需要确认 | 需要人工审核 |
| `hybrid` | 有更新才同步 | 减少不必要的同步 |

### 输出格式

```
当前策略: hybrid
─────────────────────────────────────
行为: 仅在有远程更新时同步

子模块状态:
  • src/thera: 无更新 (已是最新)
  • docs/archive: 有更新 (可同步)
─────────────────────────────────────
```

---

## 实现计划

### Phase 1: workflow status (P0)

1. 实现 `WorkflowEngine.get_status()` 返回状态信息
2. 实现 `WorkflowEngine.get_error_details()` 返回错误详情
3. 添加 CLI `workflow status` 命令
4. 添加测试

### Phase 2: workflow history (P1)

1. 实现 `WorkflowEngine.get_history()` 返回历史记录
2. 添加 CLI `workflow history` 命令
3. 添加测试

### Phase 3: workflow audit (P2)

1. 实现 `WorkflowEngine.audit()` 生成审计报告
2. 添加 CLI `workflow audit` 命令
3. 添加测试

### Phase 4: --strategy (P1)

1. 实现 `WorkflowEngine.set_strategy()` 设置策略
2. 修改 `sync_submodules()` 使用策略
3. 添加 CLI `--strategy` 参数
4. 添加测试

---

## 技术实现

### WorkflowEngine 新增方法

```python
class WorkflowEngine:
    def get_status(self) -> dict:
        """获取状态信息"""
        
    def get_error_details(self) -> Optional[dict]:
        """获取错误详情"""
        
    def get_history(self, limit: int = 10) -> list[dict]:
        """获取状态历史"""
        
    def audit(self, since: datetime, until: datetime) -> dict:
        """生成审计报告"""
        
    def set_strategy(self, strategy: ConvergenceStrategy):
        """设置收敛策略"""
```

### CLI 新增命令

```python
# workflow 子命令
workflow_parser = subparsers.add_parser("workflow", help="工作流相关命令")
workflow_subparsers = workflow_parser.add_subparsers(dest="workflow_command")

# status
status_parser = workflow_subparsers.add_parser("status", help="查看当前状态")

# history
history_parser = workflow_subparsers.add_parser("history", help="查看状态历史")
history_parser.add_argument("--limit", type=int, default=10)

# audit
audit_parser = workflow_subparsers.add_parser("audit", help="生成审计报告")
audit_parser.add_argument("--since", help="开始日期")
audit_parser.add_argument("--until", help="结束日期")
```

---

## 相关文档

- [架构设计](./architecture.md)
- [状态机设计](./fsm-design.md)
- [测试报告](../test-report.md)
