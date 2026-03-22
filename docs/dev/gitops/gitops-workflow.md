# 工作流设计

## 1. 设计原则

**极简主义**：单一命令完成所有操作，无需用户理解复杂状态机。

## 2. 命令设计

### 2.1 refresh

`refresh` 是 thera 的唯一命令，完成以下操作：

1. 检测所有子模块更新
2. 拉取最新
3. 提交主仓库变更（子模块指针变化）
4. 推送到远程

```bash
thera refresh              # 完整流程
thera refresh --dry-run   # 预览
```

### 2.2 设计决策

| 决策 | 选择 | 理由 |
|------|------|------|
| 单一命令 | refresh | 用户只需记住一个命令 |
| 集成推送 | 是 | 提交后几乎总是要推送 |
| 预览模式 | --dry-run | 提供安全的预览能力 |
| 状态机 | 不需要 | Git 状态已足够透明 |

## 3. 实现

```python
def refresh(repo_root: Path, dry_run: bool = False) -> RefreshResult:
    """
    同步子模块并提交推送主仓库
    """
    ops = GitOps(repo_root)
    
    # 1. 检测子模块更新
    submodule_status = ops.get_submodule_status()
    
    # 2. 拉取最新（如果有更新）
    for sm in submodule_status:
        if sm.behind:
            ops.update_submodule(sm.path)
    
    # 3. 检查是否有变更需要提交
    status = ops.get_status()
    if not status.is_clean:
        if dry_run:
            return RefreshResult(
                success=True,
                dry_run=True,
                message=f"将提交 {len(status.changes)} 个变更"
            )
        # 4. 提交并推送
        result = ops.commit_and_push("chore(submodule): sync submodules")
        return result
    
    return RefreshResult(success=True, message="已是最新")
```

## 4. 与旧设计对比

| 旧设计 | 新设计 |
|--------|--------|
| doc-check → submodule-sync → auto-commit | refresh |
| 三步流程 | 一步完成 |
| 状态机 M0-M4 | 无状态机 |
| 范畴论工作流 | 简单函数 |
