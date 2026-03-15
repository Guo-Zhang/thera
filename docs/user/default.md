# 默认活动使用教程

## 运行

```bash
cd platform
PYTHONPATH=src python -m thera.cli <日志文件路径>
```

## 示例

```bash
PYTHONPATH=src python -m thera.cli ../journal/default/2026-03-15.md
```

## 输出

处理后的文件会在每个段落末尾添加 AI 批注：

```
原文内容...

> 🤖 观察者注
> 🏷️ 标签：#分类1 #分类2
> 💎 提炼：提取的标准化知识
```
