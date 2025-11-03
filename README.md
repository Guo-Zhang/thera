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
│       ├── __main__.py # 命令行入口
│       └── cli.py      # 交互式命令行实现
├── tests/             # 测试目录
│   ├── __init__.py
│   └── test_cli.py    # CLI模块测试
├── data/              # 数据目录
├── docs/             # 文档目录
├── pyproject.toml    # 项目配置
└── README.md         # 项目说明
```

## 开发

要添加新的命令行功能，在 `src/thera/cli.py` 中的 `TheraCLI` 类添加新的命令方法。例如，添加一个名为 `hello` 的命令：

```python
def do_hello(self, arg):
    """打招呼"""
    print("你好！")
```

## 测试

本项目使用 pytest 进行测试。测试用例位于 `tests` 目录下。

### 安装测试依赖

```bash
pip install -e ".[test]"
```

### 运行测试

运行所有测试：
```bash
pytest
```

查看测试覆盖率报告：
```bash
pytest --cov=thera --cov-report=term-missing
```

### 编写测试

新的测试用例应该添加到 `tests` 目录中。测试文件命名应遵循 `test_*.py` 的模式。例如：

```python
import unittest
from thera.cli import TheraCLI

class TestNewFeature(unittest.TestCase):
    def setUp(self):
        self.cli = TheraCLI()
    
    def test_new_command(self):
        """测试新命令"""
        result = self.cli.do_new_command("")
        self.assertEqual(result, expected_result)
```

