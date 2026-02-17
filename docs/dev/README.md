# 开发者文档

## 目标

记录 thera 的架构设计、模块实现、开发约束与经验沉淀。

## 开发命令

```bash
# 安装依赖
uv sync --dev

# 运行所有测试
uv run pytest -v

# 运行特定测试
uv run pytest tests/test_think_domain.py -v

# 运行审计脚本
uv run python scripts/audit.py
```

## 核心模块

- 入口：`src/thera/__main__.py`
- 元模型：`src/thera/meta.py`
- Domain：`src/thera/domain/`
- Infra：`src/thera/infra/`
- Activity：`src/thera/activity/`
- State：`src/thera/state/`

## 文档入口

- 活动模块：`docs/dev/activity/`
- 基础设施模块：`docs/dev/infra/`
- 领域设计：`docs/dev/domain/`
- 元模型说明：`docs/dev/meta.md`
- 主流程说明：`docs/dev/main.md`

## 维护约定

- 新增/重构模块后，补充对应 `docs/dev/` 文档
- 文档记录实现逻辑与经验，不记录一次性运行输出
- 输出报告放到 `data/activity/<module>/` 或 `docs/ops/reports/`
