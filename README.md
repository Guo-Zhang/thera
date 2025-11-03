# `thera`

苹果的AI外脑系统

## 安装

本项目需要 Python 3.14 或更高版本。

### 开发环境安装

1. 克隆项目：
```bash
git clone https://github.com/Guo-Zhang/thera.git
cd thera
```

2. 创建并激活虚拟环境（推荐）：
```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate
```

3. 安装开发版本：
```bash
pip install -e .
```

## 使用方法

安装完成后，可以通过命令行使用 `thera` 命令：

### 基本命令

1. 显示帮助信息：
```bash
thera
```

2. 查看版本：
```bash
thera --version
```

## 项目结构

```
thera/
├── src/
│   └── thera/          # 主程序包
│       ├── __init__.py
│       └── __main__.py # 命令行入口
├── data/               # 数据目录
├── docs/              # 文档目录
├── pyproject.toml     # 项目配置
└── README.md          # 项目说明
```

## 开发

要添加新的命令行功能，在 `src/thera/__main__.py` 中的 `main()` 函数添加相应的命令处理逻辑即可。

