# 用户指南

## 工具概览

Thera 提供三个命令行工具，用于管理 quanttide-founder 的数字资产：

| 工具 | 用途 | 典型场景 |
|------|------|----------|
| [auto-commit](auto-commit.md) | 自动提交推送 | 修改代码后一键提交到云端 |
| [doc-check](doc-check.md) | 文档一致性检查 | 验证 YAML 与 .gitmodules 一致性 |
| [submodule-sync](submodule-sync.md) | 子模块同步 | 拉取子模块远程更新 |

## 快速开始

```bash
# 设置 PYTHONPATH
export PYTHONPATH=src/thera/src

# 查看帮助
python3 src/thera/src/thera/cli.py --help
```

## 推荐工作流

```
1. 修改代码/文档
2. doc-check    → 验证一致性
3. submodule-sync --check  → 检测远程更新
4. submodule-sync --sync-all  → 同步子模块（如有更新）
5. auto-commit  → 提交并推送
```

## 变更类型识别

| 类型前缀 | 检测文件 |
|----------|----------|
| `docs` | `docs/` 目录 |
| `code` | `src/` 目录 |
| `config` | `.gitmodules`, `.gitignore` |
| `meta` | `meta/` 目录 |
| `root` | 根目录文件 |
