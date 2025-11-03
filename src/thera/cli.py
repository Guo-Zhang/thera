"""
Thera 命令行交互模式实现
"""
import cmd
import sys


class TheraCLI(cmd.Cmd):
    """Thera 交互式命令行界面"""
    
    intro = "欢迎使用 Thera AI外脑系统。输入 help 或 ? 查看帮助。"
    prompt = "thera> "
    
    def do_exit(self, arg):
        """退出 Thera"""
        print("再见！")
        return True
        
    def do_quit(self, arg):
        """退出 Thera"""
        return self.do_exit(arg)
        
    def do_EOF(self, arg):
        """使用 Ctrl-D (Unix) 或 Ctrl-Z (Windows) 退出"""
        print()  # 打印空行
        return self.do_exit(arg)
        
    def emptyline(self):
        """空行时不重复执行上一条命令"""
        pass
    
    def do_version(self, arg):
        """显示当前版本"""
        try:
            from importlib.metadata import version
            print(f"Thera version {version('thera')}")
        except Exception as e:
            print(f"无法获取版本信息: {e}")


def start_cli():
    """启动交互式命令行界面"""
    try:
        TheraCLI().cmdloop()
    except KeyboardInterrupt:
        print("\n再见！")
        sys.exit(0)
