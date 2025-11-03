"""
Thera 命令行入口文件
"""
import sys
from .cli import start_cli


def main():
    """
    主函数，处理命令行参数并执行相应的操作
    """
    args = sys.argv[1:]
    
    # 处理命令行参数
    if args:
        command = args[0]
        if command == "--version":
            from importlib.metadata import version
            print(f"Thera version {version('thera')}")
            return
        print(f"未知命令: {command}")
        print("提示：直接运行 thera 进入交互模式")
        return
    
    # 无参数时启动交互模式
    start_cli()


if __name__ == "__main__":
    main()
