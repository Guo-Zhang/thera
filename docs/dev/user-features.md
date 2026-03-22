# 用户功能设计文档

**日期**: 2026-03-22
**范围**: refresh 命令

---

## 概述

基于极简原则设计，thera 只有两个命令：

| 命令 | 功能 |
|------|------|
| `thera refresh` | 同步子模块 + 提交 + 推送 |
| `thera refresh --dry-run` | 预览变更，不执行 |

---

## refresh

### 命令行接口

```bash
thera refresh [--dry-run] [--repo PATH]
```

### 选项

| 选项 | 说明 |
|------|------|
| `--dry-run` | 预览模式，不执行实际变更 |
| `--repo PATH` | 指定仓库路径（默认当前目录） |

### 输出格式

```
正在同步子模块...
✓ docs/journal: 已更新到 abc1234
✓ src/thera: 无更新
✓ packages/devops: 已更新到 def5678

提交变更中...
✓ 已提交并推送

变更摘要:
  - 3 个子模块已更新
  - 1 个提交已推送
```

### 预览模式输出

```
[预览模式] 以下变更将被执行:

子模块更新:
  • docs/journal: abc1234 → xyz9999
  • packages/devops: def5678 → uvw1111

将提交的变更: 2 个
```

---

## 实现

```python
# refresh 命令
@click.command()
@click.option('--dry-run', is_flag=True, help='预览模式')
@click.option('--repo', default='.', help='仓库路径')
def refresh(dry_run: bool, repo: str):
    """同步子模块并提交推送"""
    repo_root = Path(repo)
    ops = GitOps(repo_root)
    
    # 检测子模块更新
    submodule_status = ops.get_submodule_status()
    updated = []
    
    for sm in submodule_status:
        if sm.behind and not dry_run:
            ops.update_submodule(sm.path)
            updated.append(sm.name)
        elif sm.behind:
            updated.append(sm.name)
    
    # 检查并提交
    status = ops.get_status()
    if not status.is_clean:
        if dry_run:
            click.echo(f"[预览] 将提交 {len(status.changes)} 个变更")
        else:
            ops.commit_and_push("chore(submodule): sync submodules")
    
    click.echo(f"✓ {len(updated)} 个子模块已更新")
```

---

## 相关文档

- [架构设计](./architecture.md)
- [工作流设计](./gitops/gitops-workflow.md)
