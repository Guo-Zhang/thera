# doc-check

检查 `.gitmodules` 与 YAML 事实源的一致性。

## 使用方法

```bash
# 进入 thera 目录
cd src/thera

# 激活虚拟环境
source .venv/bin/activate

# 使用默认配置
python src/thera/cli.py doc-check

# 指定配置文件
python src/thera/cli.py doc-check --config meta/profile/submodules.yaml
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
$ python src/thera/cli.py doc-check
[OK] 一致性检查通过

# 发现问题
$ python src/thera/cli.py doc-check
[WARN] 一致性检查失败: 缺失路径: docs/archive
```

## 退出码

| 退出码 | 含义 |
|--------|------|
| 0 | 检查通过 |
| 1 | 有缺失或不一致 |

## 状态机集成

doc-check 与状态机集成：

- 检查通过 → 状态转移至 CLEAN_AND_CONSISTENT
- 检查失败 → 状态转移至 INCONSISTENT
