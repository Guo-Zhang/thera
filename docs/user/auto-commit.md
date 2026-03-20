# auto-commit

自动检测变更并提交推送，支持主仓库和子模块。

## 使用方法

```bash
# 进入 thera 目录
cd src/thera

# 激活虚拟环境
source .venv/bin/activate

# 仅显示变更（不提交）
python src/thera/cli.py auto-commit --dry-run

# 交互式提交推送
python src/thera/cli.py auto-commit
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

## 退出码

| 退出码 | 含义 |
|--------|------|
| 0 | 全部成功 |
| 1 | 有操作失败 |

## 示例

```bash
# 检测变更
$ python src/thera/cli.py auto-commit --dry-run
Detected changes:
--------------------------------------------------
主仓库: 2 个文件
  MODIFIED: src/thera/cli.py
  UNTRACKED: scripts/
--------------------------------------------------

Dry run - no changes made.

# 实际提交
$ python src/thera/cli.py auto-commit
Detected changes:
--------------------------------------------------
主仓库: 2 个文件
  MODIFIED: src/thera/cli.py
  UNTRACKED: scripts/
--------------------------------------------------

Commit and push these changes? [y/N/q]: y
>>> 处理 主仓库...
[OK] 主仓库 pushed

[ALL DONE] All changes committed and pushed.
```

## 状态机集成

auto-commit 与状态机集成，确保操作的安全性：

- 在非 SYNCED 状态下，自动触发状态转移
- 推送失败时进入错误状态，便于问题排查
