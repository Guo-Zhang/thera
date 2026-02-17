# Thera 系统自画像

- **生成时间**: 2026-02-18 01:28:34

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
- src/thera/domain/knowl.py:12: unused import 'get_embedding' (90% confidence)
- src/thera/domain/knowl.py:12: unused import 'llm_chat_str' (90% confidence)
- src/thera/domain/knowl.py:12: unused import 'llm_stream' (90% confidence)
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
- 高度结构化的策略意识：明确定义了人机协作范式、工作流程、权限边界和版本更新逻辑，具备清晰的元策略层级（原则→流程→边界→规范）
- 强调整体系统一致性与动态维护机制：如‘README 是 single source of truth’‘修改代码前先核对约定’‘更新代码需同步更新文档’，体现对认知闭环的主动设计

**建议:**
- 在‘工作流程’或‘协作约束’中嵌入显式监控节点，例如：‘步骤4执行操作后，自动校验变更文件列表与需求范围是否一致；不一致则中断并生成差异报告’
- 在关键规范旁添加‘元注释块’（如 > 💡 元认知说明：本条源于上一迭代中3次 README-代码不一致引发的部署故障，现固化为预防性策略），将隐性经验转化为显性自我反思