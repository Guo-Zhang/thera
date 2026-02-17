# AGENTS

本文件只保留 AI/代理协作约束；项目通用说明统一放在 `README.md`。

## 参考顺序

1. 先看 `README.md`（命令、架构、环境变量、数据规则）。
2. 再看 `docs/RAEDME.md` 和 `docs/dev/README.md` 获取细节。

## 协作约束

- 修改代码前，先核对 `README.md` 的当前约定。
- 若发现 README 与代码不一致，优先在同一变更中更新 `README.md`。
- 涉及用户数据（移动、删除、重命名）前必须先确认。
- 未经明确要求，不执行破坏性操作（如批量删除、重置历史）。

## 文档入口

- 项目文档索引：`docs/RAEDME.md`
- 开发文档：`docs/dev/README.md`
- 用户指南：`docs/user/README.md`
- 运维文档：`docs/ops/README.md`

## 文档一致性要求

- README 是项目入口真相源（single source of truth）。
- AGENTS 不重复维护命令清单、架构细节、环境变量；这些内容仅维护在 README。
- 后续若发现说明不准确，请及时修正 `README.md`，并保持本文件最小化。

## 数据安全规则

- 涉及用户数据的移动、删除、重命名前，先确认。
- 避免直接使用破坏性删除命令，优先先检查再操作。
- 重要数据操作前先确认文件存在，必要时先备份。
- 优先读取数据，修改写入前再次确认影响范围。

## 文档维护约定

- 功能新增或重构后，及时更新 `README.md` 与对应 `docs/dev/` 文档。
- `README.md` 作为项目入口文档，应与当前代码结构和命令保持一致。
- 运行结果与报告不写入 README，放在 `data/` 或 `docs/ops/reports/`。
