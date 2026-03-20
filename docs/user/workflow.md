# workflow

工作流相关命令，查看状态、历史和审计报告。

## workflow status

查看当前仓库状态和允许的操作。

```bash
python src/thera/cli.py workflow status
```

### 输出示例

```
当前状态: DIRTY
------------------------------------------------------------
变更: 3 个文件待提交

允许操作:
  • DOC_CHECK_OK
  • DOC_CHECK_FAIL
------------------------------------------------------------
状态转移历史: 0 次
```

### 状态颜色

| 状态 | 颜色 | 说明 |
|------|------|------|
| DIRTY | 红色 | 有变更未提交 |
| CLEAN_AND_CONSISTENT | 绿色 | 干净且一致 |
| INCONSISTENT | 黄色 | 配置不一致 |
| SYNCED | 蓝色 | 子模块已同步 |
| COMMITTED | 绿色 | 变更已提交 |
| ERROR | 红色 | 错误状态 |

---

## workflow history

查看状态转移历史记录。

```bash
python src/thera/cli.py workflow history [--limit N]
```

### 参数

| 参数 | 说明 |
|------|------|
| `--limit N` | 显示条数（默认 10） |

### 输出示例

```
状态历史 (最近 5 条)
------------------------------------------------------------
  DIRTY                → DOC_CHECK_OK
  CLEAN_AND_CONSISTENT → SUBMODULE_SYNC
  SYNCED               → AUTO_COMMIT
  COMMITTED             → PUSH_OK
  COMMITTED             → DIRTY
------------------------------------------------------------
总计: 5 次状态转移
```

---

## workflow audit

生成审计报告，包括状态分布和错误统计。

```bash
python src/thera/cli.py workflow audit [--since DATE] [--until DATE]
```

### 参数

| 参数 | 说明 |
|------|------|
| `--since DATE` | 开始日期 (YYYY-MM-DD) |
| `--until DATE` | 结束日期 (YYYY-MM-DD) |

### 输出示例

```
审计报告
================================================================================
概览
------------------------------------------------------------
状态转移: 47 次
错误次数: 2 次

状态分布
------------------------------------------------------------
  DIRTY                  ████████████████████ 60%
  CLEAN_AND_CONSISTENT  ██████████          30%
  SYNCED                ██                   6%
  COMMITTED             █                     3%
  ERROR                 ▏                    1%

错误详情
------------------------------------------------------------
  • NETWORK_ERROR - PUSH_FAIL
  • CONSISTENCY_ERROR - DOC_CHECK_FAIL
================================================================================
```

---

## --strategy 收敛策略

控制子模块同步的收敛行为。

```bash
python src/thera/cli.py auto-commit --strategy={auto|manual|hybrid}
```

### 策略说明

| 策略 | 行为 | 适用场景 |
|------|------|----------|
| `auto` | 总是自动同步 | 信任子模块，可自动化 |
| `manual` | 需要确认 | 需要人工审核 |
| `hybrid` | 有更新才同步 | 减少不必要的同步 |

### 示例

```bash
# 自动模式（默认）
python src/thera/cli.py auto-commit --strategy=auto

# 手动模式
python src/thera/cli.py auto-commit --strategy=manual

# 混合模式
python src/thera/cli.py auto-commit --strategy=hybrid
```
