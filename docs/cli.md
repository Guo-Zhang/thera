# 命令行接口

## 基本用法

### 命令行模式

1. 查看版本：
```bash
thera --version
```

### 交互模式

输入 `thera` 不带参数，进入交互式命令行界面：

```bash
$ thera
欢迎使用 Thera AI外脑系统。输入 help 或 ? 查看帮助。
thera>
```

## 可用命令

在交互模式下可以使用以下命令：

### 帮助命令
- `help` 或 `?`: 显示帮助信息
- `help 命令`: 显示特定命令的帮助信息

### 系统命令
- `version`: 显示当前版本号
- `exit` 或 `quit`: 退出程序
- Ctrl-D (Unix) 或 Ctrl-Z (Windows): 退出程序

### 交互特性
- 空行: 按 Enter 键不会重复上一条命令
- 命令补全: 使用 Tab 键可以补全命令
- 历史记录: 使用上下方向键可以浏览历史命令

## 开发新命令

要添加新的命令，在 `TheraCLI` 类中添加以 `do_` 开头的方法。例如：

```python
def do_hello(self, arg):
    """
    打招呼命令
    使用方法: hello [名字]
    """
    name = arg.strip() or "世界"
    print(f"你好，{name}！")
```

该命令可以这样使用：
```bash
thera> hello
你好，世界！
thera> hello 小明
你好，小明！
```

### 命令规范

1. 方法名必须以 `do_` 开头
2. 方法必须接受 `self` 和 `arg` 两个参数
3. 文档字符串用于生成帮助信息
4. 返回 `True` 将退出程序
5. 返回 `False` 或 `None` 继续交互循环
