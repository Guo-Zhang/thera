# 迁移步骤

## 概述

从当前架构迁移到目标架构的详细步骤。采用验证性重构策略，确保安全性和行为一致性。

## 迁移原则

1. **行为优先**：新代码必须与旧代码行为完全一致
2. **渐进替换**：I/O 层先行，逻辑层在后
3. **持续验证**：每个阶段完成后立即测试
4. **可回滚**：保留旧代码直到新代码完全验证通过

## 已完成工作

| 组件 | 状态 | 说明 |
|------|------|------|
| fsm.py | ✅ 完成 | 状态机核心 (RepoState, Event, StateMachine) |
| git_ops.py | ✅ 完成 | Git 操作封装层 |
| workflow.py | ✅ 完成 | 工作流引擎 (WorkflowEngine, ConvergenceStrategy) |
| test_fsm.py | ✅ 完成 | 28 测试，100% 覆盖率 |
| test_git_ops.py | ✅ 完成 | 45 测试，94% 覆盖率 |
| test_workflow.py | ✅ 完成 | 21 测试，94% 覆盖率 |

---

## 阶段一：行为基准（Diff 测试）

**目标**: 证明新领域层与旧应用层行为完全一致。

### 1.1 创建对比测试

```python
# tests/test_behavior_parity.py
@pytest.mark.parametrize("scenario", [
    "clean_repo",
    "modified_file", 
    "untracked_file",
    "submodule_dirty",
    "submodule_clean",
])
def test_get_status_parity(scenario, repo_fixture):
    """验证 get_status() 行为一致"""
    from auto_commit import get_repo_status as old_get_status
    from git_ops import GitOps as new_git_ops
    
    # 旧实现
    old_result = old_get_status(repo_fixture.path)
    
    # 新实现
    ops = new_git_ops(repo_fixture.path)
    new_result = ops.get_status()
    
    # 断言完全一致
    assert old_result.is_clean == new_result.is_clean
    assert len(old_result.changes) == len(new_result.changes)
    for old_c, new_c in zip(old_result.changes, new_result.changes):
        assert old_c.path == new_c.path
        assert old_c.change_type == new_c.change_type
```

### 1.2 运行 Diff 测试

```bash
python -m pytest tests/test_behavior_parity.py -v

# 必须全部通过，否则不能进入下一阶段
```

### 1.3 验证清单

- [ ] get_status() 行为一致
- [ ] get_submodule_status() 行为一致
- [ ] check_consistency() 行为一致
- [ ] commit_and_push() 行为一致
- [ ] sync_submodules() 行为一致

---

## 阶段二：影子模式验证

**目标**: 在真实环境中并行运行新旧代码，仅报警不阻断。

### 2.1 添加影子模式开关

```python
# cli.py
def main():
    args = parser.parse_args()
    
    # 新增 --new-engine 开关
    use_new_engine = getattr(args, 'new_engine', False)
    
    if args.command == "auto-commit":
        if use_new_engine:
            # 影子模式：新逻辑运行但不执行副作用
            from workflow import WorkflowEngine
            engine = WorkflowEngine(repo_root)
            result = engine.commit_and_push(args.message)
            # 打印结果但不实际提交
            print(f"[影子模式] 结果: {result}")
            return 0
        
        # 旧逻辑（实际执行）
        from auto_commit import main as old_main
        return old_main()
```

### 2.2 自动化对比脚本

```bash
#!/bin/bash
# scripts/shadow_verify.sh

REPO=$1
cd $REPO

echo "=== 影子模式验证 ==="
echo "旧逻辑: auto-commit --dry-run"
python -m thera auto-commit --dry-run 2>&1

echo ""
echo "新逻辑: auto-commit --dry-run --new-engine"
python -m thera auto-commit --dry-run --new-engine 2>&1

echo ""
read -p "结果是否一致？ (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "验证失败，停止迁移"
    exit 1
fi
```

### 2.3 验证清单

- [ ] 影子模式正常输出
- [ ] 新旧结果人工对比一致
- [ ] 无异常或错误
- [ ] 连续运行 3 次行为稳定

---

## 阶段三：分层替换

### 3.1 阶段 3A：替换 I/O 调用

**策略**: 保持流程不变，只替换底层 git 命令调用。

```python
# auto_commit.py (过渡版本)

# 删除 run_git() 函数
# def run_git(args, repo_root, capture=True):
#     ...

# 改为导入 GitOps
from git_ops import GitOps

def main():
    ops = GitOps(repo_root)  # 使用新封装
    
    # 原有流程代码保持不变
    status = ops.get_status()  # 替换 get_repo_status()
    changes = ops.get_submodule_status()  # 替换 get_submodule_status()
    # ...
```

**验证**: 运行 `python -m pytest tests/test_auto_commit.py -v`

### 3.2 阶段 3B：替换流程控制

**策略**: 将 if/else 判断迁移到 WorkflowEngine。

```python
# cli.py
def main():
    from workflow import WorkflowEngine
    
    engine = WorkflowEngine(repo_root)
    
    if args.command == "doc-check":
        result = engine.doc_check(Path(args.yaml))
        return 0 if result.is_consistent else 1
    
    elif args.command == "submodule-sync":
        result = engine.sync_submodules(args.paths)
        return 0 if result.success else 1
    
    elif args.command == "auto-commit":
        result = engine.commit_and_push(args.message)
        return 0 if result.success else 1
```

**验证**: 运行 `python -m pytest tests/ -v`

---

## 阶段四：切换主入口

### 4.1 更新 CLI 入口

```python
# cli.py
def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='command')
    
    # 新的统一命令结构
    add_common_args(subparsers)
    
    # 原有命令保留别名
    subparsers.add_parser('check', help='等价于 doc-check')
    subparsers.add_parser('sync', help='等价于 submodule-sync')
    subparsers.add_parser('commit', help='等价于 auto-commit')
```

### 4.2 废弃旧函数

```python
# auto_commit.py

def run_git(*args, **kwargs):
    """废弃：使用 GitOps.run_git() 替代"""
    import warnings
    warnings.warn(
        "run_git() 已废弃，请使用 GitOps.run_git()",
        DeprecationWarning,
        stacklevel=2
    )
    from git_ops import GitOps
    ops = GitOps(Path.cwd())
    return ops.run_git(*args, **kwargs)
```

### 4.3 验证清单

- [ ] 所有 CLI 命令正常工作
- [ ] 废弃警告正常触发
- [ ] 无回归测试失败

---

## 阶段五：清理与增强

### 5.1 删除废弃代码

```bash
# 确认所有调用已迁移后
git rm src/thera/auto_commit.py
git rm src/thera/doc_check.py
git rm src/thera/submodule_sync.py
```

### 5.2 添加状态钩子

```python
# fsm.py
@dataclass
class StateMachine:
    on_enter_callbacks: dict[RepoState, list] = field(default_factory=dict)
    on_exit_callbacks: dict[RepoState, list] = field(default_factory=dict)
    
    def add_enter_hook(self, state: RepoState, callback):
        if state not in self.on_enter_callbacks:
            self.on_enter_callbacks[state] = []
        self.on_enter_callbacks[state].append(callback)
```

### 5.3 添加事务性语义

```python
# workflow.py
def run_standard_workflow(self, yaml_path: Path) -> WorkflowResult:
    """带事务性语义的工作流"""
    checkpoints = []
    
    try:
        # 1. 一致性检查
        doc_result = self.doc_check(yaml_path)
        if not doc_result.is_consistent:
            return WorkflowResult(success=False, message="一致性检查失败")
        checkpoints.append("doc_check")
        
        # 2. 子模块同步
        sync_result = self.sync_submodules()
        if not sync_result.success:
            self._rollback_sync(checkpoints)
            return WorkflowResult(success=False, message="同步失败")
        checkpoints.append("sync")
        
        # 3. 提交推送
        push_result = self.commit_and_push()
        if not push_result.success:
            return WorkflowResult(success=False, message="推送失败")
        
        return WorkflowResult(success=True, message="工作流完成")
    
    except Exception as e:
        self._emergency_rollback(checkpoints)
        return WorkflowResult(success=False, message=f"异常: {e}")
```

### 5.4 验证清单

- [ ] 旧代码已删除
- [ ] 新增功能正常工作
- [ ] 完整测试通过
- [ ] 覆盖率 ≥ 95%

---

## 验证总清单

| 阶段 | 验证项 | 状态 |
|------|--------|------|
| 一 | Diff 测试全部通过 | ⬜ |
| 二 | 影子模式验证成功 | ⬜ |
| 三 | 分层替换无回归 | ⬜ |
| 四 | CLI 入口切换完成 | ⬜ |
| 五 | 清理增强完成 | ⬜ |

---

## 回滚方案

如遇问题，按以下顺序回滚：

1. **阶段一回滚**: 禁用 Diff 测试，继续使用旧代码
2. **阶段二回滚**: 关闭 `--new-engine` 开关
3. **阶段三回滚**: 恢复旧函数调用
4. **阶段四回滚**: 恢复 CLI 旧入口
5. **阶段五回滚**: `git revert` 删除操作

---

## 相关文档

- [架构设计](./architecture.md)
- [状态机设计](./fsm-design.md)
- [Git 操作层设计](./git-ops-design.md)
- [工作流设计](./gitops-workflow.md)
- [重构策略](./refactor.md)
- [测试报告](../test-report.md)
