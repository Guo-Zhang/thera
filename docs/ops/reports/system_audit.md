# Thera 系统自画像

- **生成时间**: 2026-02-18 01:11:09

## 1. 复杂度热点 (Radon)

| 函数 | 复杂度 |
| --- | --- |
| StorageState._validate_path | 4 |
| StorageState.ensure_dirs | 4 |
| StorageState.load_json | 4 |
| StorageState.load_yaml | 4 |
| Thera.__init__ | 4 |
| Thera.domain_manager | 4 |
| Thera.storage | 4 |
| Thera.switch_domain | 4 |

## 2. 僵尸代码 (Vulture)

- src/thera/activity/memo.py:18: unused import 'generate_reasoning_report' (90% confidence)
- src/thera/activity/memo.py:25: unused import 'llm_analyze_direction' (90% confidence)
- src/thera/domain/knowl.py:16: unused import 'get_embedding' (90% confidence)
- src/thera/domain/knowl.py:16: unused import 'llm_chat_str' (90% confidence)
- src/thera/domain/knowl.py:16: unused import 'llm_stream' (90% confidence)
- src/thera/infra/feishu.py:16: unused import 'time' (90% confidence)

## 3. 依赖关系 (Pyan3)

_无依赖数据_

## 4. 元认知浓度 (LLM)

**总分: 7/10**

- 自我意识: 6/10
- 策略意识: 9/10
- 监控意识: 5/10
- 评估意识: 7/10
- 调整意识: 8/10

**优势:**
- 高度结构化的策略显性化（如‘最小干预’‘查询 index→执行→更新 index→验证’闭环流程）
- 强调整体系统一致性与责任边界（如 README 作为 single source of truth、权限分级、版本语义驱动变更决策）

**建议:**
- 在‘工作流程’中嵌入元认知提示点，例如在‘检查现状’后增加‘若配置逻辑模糊，主动请求用户澄清或标记不确定性’
- 补充轻量级监控契约，如‘每次修改前记录预期影响范围；修改后对比 diff 并标注高风险变更项’，将隐性评估显性化为可审计动作