# 运维文档

## 审计脚本

```bash
uv run python scripts/audit.py
```

脚本用途：对 `AGENTS.md` 执行元认知审计并生成报告。

## 报告路径

- 最新报告：`docs/ops/reports/report.json`

## 运维检查清单

- 依赖是否完成安装：`uv sync --dev`
- 环境变量是否完整：`.env`
- 关键测试是否通过：`uv run pytest -v`
- 审计是否成功生成报告：`docs/ops/reports/report.json`

## 故障排查

- 如果脚本运行失败，先检查 Python 环境与依赖版本
- 如果报告为空，检查输入文档路径和读取权限
- 如果涉及外部 API，检查网络与密钥配置
