# 默认活动使用教程

## 安装依赖

```bash
cd platform
pip install pydantic-settings pyyaml
```

## 配置文件

复制配置示例文件：

```bash
cp config.example.yaml config.yaml
```

根据需要编辑 `config.yaml`，默认配置：

```yaml
opencode_path: /usr/local/bin/opencode
model: o4-mini
max_retries: 3
```

## 运行

```bash
# 方式1：使用启动脚本
./scripts/default.sh <日志文件路径>

# 方式2：直接运行
PYTHONPATH=src python -m thera <日志文件路径>
```

## 示例

```bash
# 处理工作日志
./scripts/default.sh ../journal/default/2026-03-15.md
```

## 输出

处理后的文件会在每个段落末尾添加 AI 批注：

```
原文内容...

> 🤖 观察者注
> 🏷️ 标签：#分类1 #分类2
> 💎 提炼：提取的标准化知识
```
