# auto-commit

自动检测变更并提交推送，支持主仓库和子模块。

## 使用方法

```bash
# 设置 PYTHONPATH
export PYTHONPATH=src/thera/src

# 仅显示变更（不提交）
python3 src/thera/src/thera/cli.py auto-commit --dry-run

# 交互式提交推送
python3 src/thera/src/thera/cli.py auto-commit
```

## 工作流程

1. **检测变更**：扫描主仓库和所有子模块的 git status
2. **显示摘要**：按变更类型分组显示
3. **确认提交**：用户输入 `y` 确认，或 `n`/`q` 退出
4. **按序推送**：先子模块后主仓库
5. **追加日志**：写入 `meta/journal/YYYY-MM-DD.md`

## 提交消息格式

| 层级 | 格式 | 示例 |
|------|------|------|
| 子模块 | `[{type}] {files}` | `[docs] README.md, tutorial/*.md` |
| 主仓库 | `[sync] [{type}] {files}, ...` | `[sync] [config] .gitmodules` |

## 日志格式

```
- 17:30 OK main: [code] src/thera, [meta] journal/*.md
```

## 退出码

| 退出码 | 含义 |
|--------|------|
| 0 | 全部成功 |
| 1 | 有操作失败 |

## 示例

```bash
# 检测变更
$ python3 src/thera/src/thera/cli.py auto-commit --dry-run
Scanning repository: /path/to/repo

Detected changes:
--------------------------------------------------
[主仓库]
  [code] src/thera, [root] README.md

[docs/tutorial]
  [root] intro.md
--------------------------------------------------

Dry run - no changes made.

# 实际提交
$ python3 src/thera/src/thera/cli.py auto-commit
...
Commit and push these changes? [y/N/q]: y
>>> 处理 docs/tutorial...
  commit: [root] intro.md...
[OK] docs/tutorial pushed

>>> 处理 主仓库...
  commit: [sync] [code] src/thera, [root] README.md...
[OK] 主仓库 pushed

[JOURNAL] Updated meta/journal/2026-03-20.md
[ALL DONE] All changes committed and pushed.
```
