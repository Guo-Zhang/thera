# doc-check

检查 `.gitmodules` 与 YAML 事实源的一致性。

## 使用方法

```bash
# 设置 PYTHONPATH
export PYTHONPATH=src/thera/src

# 使用默认配置
python3 src/thera/src/thera/cli.py doc-check

# 指定配置文件
python3 src/thera/src/thera/cli.py doc-check --config meta/profile/submodules.yaml
```

## 检查内容

1. **名称一致性**：YAML 中的 name 与 .gitmodules 中的 path 是否匹配
2. **路径存在性**：YAML 中声明的路径是否真实存在

## YAML 格式要求

```yaml
submodules:
  - name: "archive"
    path: "docs/archive"
    url: "https://github.com/quanttide/..."
  - name: "thera"
    path: "src/thera"
    url: "https://github.com/..."
```

## 示例

```bash
$ python3 src/thera/src/thera/cli.py doc-check
============================================================
文档一致性检查
============================================================
仓库: /path/to/repo
配置文件: meta/profile/submodules.yaml

检查 .gitmodules 与 YAML 事实源一致性...
  [OK] 12 个路径

所有检查通过
```

## 退出码

| 退出码 | 含义 |
|--------|------|
| 0 | 检查通过 |
| 1 | 有缺失或不一致 |
