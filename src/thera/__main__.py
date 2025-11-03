"""
Thera 命令行入口文件
"""
import sys


def main():
    """
    主函数，处理命令行参数并执行相应的操作
    """
    args = sys.argv[1:]
    if not args:
        print("欢迎使用 Thera!")
        print("使用方法: thera [命令] [参数]")
        return

    command = args[0]
    if command == "--version":
        from importlib.metadata import version
        print(f"Thera version {version('thera')}")
    else:
        print(f"未知命令: {command}")
        print("使用方法: thera [命令] [参数]")


if __name__ == "__main__":
    main()
