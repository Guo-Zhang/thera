# 测试设计与实现报告

**日期**: 2026-03-20
**更新**: 2026-03-20（包含全部测试套件）

---

## 概览

本项目测试套件覆盖 FSM 层、GitOps 层、Workflow 层及原有功能模块，采用 TDD 范式。

| 测试文件 | 模块 | 测试数 | 覆盖率 |
|----------|------|--------|--------|
| `test_auto_commit.py` | 现有 - 自动提交 | 55 | 99% |
| `test_doc_check.py` | 现有 - 文档检查 | 17 | 99% |
| `test_integration.py` | 现有 - 集成测试 | 6 | - |
| `test_submodule_sync.py` | 现有 - 子模块同步 | 17 | 99% |
| `test_fsm.py` | 新增 - 状态机 | 28 | 100% |
| `test_git_ops.py` | 新增 - Git 操作封装 | 45 | 94% |
| `test_workflow.py` | 新增 - 工作流引擎 | 21 | 94% |
| **总计** | - | **184** | **94%** |

---

## 测试文件详情

### test_auto_commit.py（现有）

55 个测试，覆盖自动提交功能的完整流程。

```
TestRunGit                    # git 命令执行
TestGetChangeType             # 变更类型识别
TestGetRepoStatus             # 仓库状态获取
TestGetSubmoduleStatus         # 子模块状态获取
TestFormatChanges             # 变更格式化
TestDetectAllChanges          # 变更检测
TestDisplayChanges            # 变更展示
TestConfirmCommit             # 提交确认
TestGenerateCommitMessage     # 提交信息生成
TestCommitAndPush             # 提交推送
TestAppendJournal             # 日志追加
TestMain                      # 主函数入口
```

### test_doc_check.py（现有）

17 个测试，覆盖 YAML 注册表与 .gitmodules 一致性检查。

```
TestLoadYamlRegistry          # YAML 加载
TestCheckGitmodulesVsYaml     # 一致性检查
TestCheckYamlPaths            # 路径验证
TestMain                      # 主函数入口
```

### test_integration.py（现有）

6 个集成测试，验证 CLI 入口点。

```
TestCliEntryPoints            # CLI 命令帮助
                            # 干运行模式
```

### test_submodule_sync.py（现有）

17 个测试，覆盖子模块同步功能。

```
TestRunGit                    # git 命令执行
TestGetSubmoduleStatus        # 子模块状态获取
TestSyncSubmodule             # 子模块同步
TestMain                      # 主函数入口
```

---

## FSM 层测试（新增）

### 目标

验证状态机核心逻辑的正确性。

### 测试用例

| 测试类 | 测试内容 |
|--------|----------|
| `TestRepoState` | 主仓库状态枚举完整性 |
| `TestSubmoduleState` | 子模块状态枚举完整性 |
| `TestErrorState` | 错误状态枚举完整性 |
| `TestEvent` | 事件枚举完整性 |
| `TestStateMachine` | 状态转移、合法性、历史记录 |
| `TestTransitionsTable` | 转移表完整性验证 |

### 状态转移表

| 当前状态 | 允许事件 | 目标状态 |
|----------|----------|----------|
| DIRTY | DOC_CHECK_OK | CLEAN_AND_CONSISTENT |
| DIRTY | DOC_CHECK_FAIL | INCONSISTENT |
| CLEAN_AND_CONSISTENT | SUBMODULE_SYNC | SYNCED |
| CLEAN_AND_CONSISTENT | FIX | DIRTY |
| INCONSISTENT | FIX | DIRTY |
| SYNCED | AUTO_COMMIT | COMMITTED |
| COMMITTED | PUSH_OK/PUSH_FAIL | COMMITTED 或 ErrorState |
| COMMITTED | EDIT | DIRTY |

### 关键测试

```python
def test_valid_transition_m0_to_m1():
    """验证 DIRTY → CLEAN_AND_CONSISTENT 转移"""
    machine = StateMachine()
    machine.transition(Event.DOC_CHECK_OK)
    assert machine.state == RepoState.CLEAN_AND_CONSISTENT

def test_illegal_transition_raises():
    """验证非法转移抛出 IllegalTransitionError"""
    machine = StateMachine()
    with pytest.raises(IllegalTransitionError):
        machine.transition(Event.AUTO_COMMIT)

def test_history_records_transitions():
    """验证历史记录正确记录转移"""
    machine = StateMachine()
    machine.transition(Event.DOC_CHECK_OK)
    assert len(machine.history) == 1
    assert machine.history[0].from_state == RepoState.DIRTY
    assert machine.history[0].to_state == RepoState.CLEAN_AND_CONSISTENT
```

---

## GitOps 层测试（新增）

### 目标

验证 Git 操作封装层的正确性。

### 测试用例

| 测试类 | 测试内容 |
|--------|----------|
| `TestChangeType` | 变更类型枚举 |
| `TestFileChange` | 文件变更数据类 |
| `TestRepoStatus` | 仓库状态数据类 |
| `TestSubmoduleInfo` | 子模块信息数据类 |
| `TestOperationResult` | 操作结果基类 |
| `TestConsistencyResult` | 一致性检查结果 |
| `TestSyncResult` | 同步结果 |
| `TestPushResult` | 推送结果 |
| `TestGitOps` | GitOps 类基础方法 |
| `TestGitOpsGetStatus` | get_status() |
| `TestGitOpsSubmoduleStatus` | get_submodule_status() |
| `TestGitOpsCheckConsistency` | check_consistency() |
| `TestGitOpsSyncSubmodules` | sync_submodules() |
| `TestGitOpsCommitAndPush` | commit_and_push() |
| `TestGitOpsRunGit` | run_git() |

### 测试策略

使用 `@patch.object` 进行单元测试，避免依赖真实的 git 仓库。

```python
@patch.object(GitOps, "run_git")
def test_nothing_to_commit(self, mock_run_git, git_ops):
    def side_effect(args):
        if args[0] == "add":
            return ("", "", 0)
        elif args[0] == "commit":
            return ("", "nothing to commit, working tree clean", 1)
        return ("", "", 0)
    mock_run_git.side_effect = side_effect
    result = git_ops.commit_and_push("test commit")
    assert result.success is True
    assert result.message == "无变更"
```

---

## Workflow 层测试（新增）

### 目标

验证工作流引擎的正确性。

### 测试用例

| 测试类 | 测试内容 |
|--------|----------|
| `TestConvergenceStrategy` | 收敛策略（Auto/Manual/Hybrid） |
| `TestWorkflowResult` | 工作流结果数据类 |
| `TestWorkflowEngine` | 工作流引擎初始化 |
| `TestWorkflowEngineDocCheck` | 一致性检查协调 |
| `TestWorkflowEngineSyncSubmodules` | 子模块同步协调 |
| `TestWorkflowEngineCommitAndPush` | 提交推送协调 |
| `TestWorkflowEngineStandardWorkflow` | 标准工作流执行 |
| `TestWorkflowEngineAppendJournal` | 日志追加 |

### 收敛策略

| 策略 | 行为 |
|------|------|
| `AutoStrategy` | 总是自动修复 |
| `ManualStrategy` | 需要人工确认 |
| `HybridStrategy` | 仅在有更新时同步 |

### 关键测试

```python
def test_standard_workflow_consistency_fail():
    """验证一致性检查失败时工作流终止"""
    workflow_engine.git_ops.check_consistency.return_value = (
        ConsistencyResult(success=False, is_consistent=False, message="不一致")
    )
    result = workflow_engine.run_standard_workflow(Path("submodules.yaml"))
    assert result.success is False
    assert "一致性检查失败" in result.message

def test_standard_workflow_sync_fail():
    """验证同步失败时工作流终止"""
    workflow_engine.git_ops.check_consistency.return_value = (
        ConsistencyResult(success=True, is_consistent=True, message="一致")
    )
    workflow_engine.git_ops.sync_submodules.return_value = SyncResult(
        success=False, message="同步失败", error="git error"
    )
    result = workflow_engine.run_standard_workflow(Path("submodules.yaml"))
    assert result.success is False
    assert "子模块同步失败" in result.message
```

---

## 覆盖率详情

```
Name                    Stmts  Miss  Cover   Missing
-----------------------------------------------------------
src/thera/__init__.py       2      0   100%
src/thera/auto_commit.py  196      1    99%   295
src/thera/cli.py           29     22    24%   20-86, 90
src/thera/doc_check.py      94      1    99%   139
src/thera/fsm.py           57      0   100%
src/thera/git_ops.py      161      9    94%   117,130,152,155,184,207-208,234,237
src/thera/submodule_sync.py 70     1    99%   104
src/thera/workflow.py       90      5    94%   34,120,164-171
-----------------------------------------------------------
TOTAL                    699     39    94%
```

### 未覆盖代码分析

| 文件 | 行号 | 说明 |
|------|------|------|
| `git_ops.py` | 117, 130 | 变更类型前缀判断 |
| `git_ops.py` | 152, 155 | 子模块状态解析 |
| `git_ops.py` | 184, 207-208, 234, 237 | 错误处理分支 |
| `workflow.py` | 34 | ConvergenceStrategy 抽象方法 |
| `workflow.py` | 120 | commit_and_push 状态处理 |
| `workflow.py` | 164-171 | 异常处理分支 |

---

## 已知问题与修复

### 1. ConsistencyResult 继承问题

**问题**: dataclass 不支持带默认值的字段继承无默认值字段。

**原始代码**:
```python
@dataclass
class OperationResult:
    success: bool
    message: str
    error: Optional[str] = None

@dataclass
class ConsistencyResult(OperationResult):  # 错误！
    is_consistent: bool  # 无默认值，跟在 Optional 后面
    missing_paths: Optional[list[str]] = None
```

**修复方案**: 使用组合而非继承。

### 2. commit_and_push 状态转移

**问题**: 需要正确处理 SYNCED → COMMITTED 转移。

**修复**:
```python
def commit_and_push(self, message: str) -> PushResult:
    if self.machine.state == RepoState.SYNCED:
        self.machine.transition(Event.AUTO_COMMIT)
    elif self.machine.state != RepoState.COMMITTED:
        if not self.machine.can_transition(Event.AUTO_COMMIT):
            return PushResult(success=False, ...)
```

---

## 运行测试

```bash
cd src/thera
source .venv/bin/activate

# 运行所有测试
python -m pytest tests/ -v

# 运行带覆盖率
python -m pytest tests/ --cov=src/thera --cov-report=term-missing

# 运行特定模块
python -m pytest tests/test_fsm.py tests/test_git_ops.py tests/test_workflow.py -v

# 运行现有测试
python -m pytest tests/test_auto_commit.py tests/test_doc_check.py -v
```

---

## 后续计划

1. **完善边界条件测试**: 增加对空输入、异常输出的测试
2. **集成测试**: 添加端到端测试验证完整流程
3. **性能测试**: 对高频操作添加性能基准测试
4. **文档**: 为每个模块添加 API 文档
