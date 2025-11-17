"""
Thera 命令行交互模式实现
"""
import cmd
import sys
import asyncio
from typing import Optional

from .main import Thera, chat_with_knowledge_sync, add_knowledge_sync, search_knowledge_sync
from .docs_importer import import_docs_cli, list_imported_docs_sync


class TheraCLI(cmd.Cmd):
    """Thera 交互式命令行界面"""

    intro = "欢迎使用 Thera AI外脑系统。输入 help 或 ? 查看帮助。"
    prompt = "thera> "

    def __init__(self):
        super().__init__()
        self.thera: Optional[Thera] = None
        self._ensure_thera_initialized()

    def _ensure_thera_initialized(self):
        """确保 Thera 客户端已初始化"""
        if self.thera is None:
            self.thera = Thera()
            # 异步初始化
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.thera.initialize())
            loop.close()

    def do_exit(self, arg):
        """退出 Thera"""
        if self.thera:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.thera.close())
            loop.close()
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

    def do_chat(self, arg):
        """与 AI 对话: chat <消息>"""
        if not arg:
            print("请输入消息。用法: chat <你的消息>")
            return

        try:
            response = chat_with_knowledge_sync(arg)
            print(f"AI: {response['response']}")
            if response['knowledge_references']:
                print(f"\n📚 参考了 {len(response['knowledge_references'])} 条知识")
        except Exception as e:
            print(f"对话失败: {e}")

    def do_add(self, arg):
        """添加知识到图谱: add "知识标题" "知识内容"""
        args = arg.split(" ", 1)
        if len(args) < 2:
            print('用法: add "知识标题" "知识内容"')
            return

        name, content = args[0], args[1]
        try:
            success = add_knowledge_sync(name, content)
            if success:
                print("✅ 知识已添加到图谱")
            else:
                print("❌ 添加知识失败")
        except Exception as e:
            print(f"添加知识失败: {e}")

    def do_search(self, arg):
        """搜索知识图谱: search <查询词>"""
        if not arg:
            print("请输入搜索词。用法: search <查询词>")
            return

        try:
            results = search_knowledge_sync(arg)
            print(f"🔍 找到 {len(results)} 条相关记录:")
            for i, result in enumerate(results, 1):
                print(f"{i}. {result['fact']}")
                if result['valid_at']:
                    print(f"   有效时间: {result['valid_at']}")
                if result['invalid_at']:
                    print(f"   失效时间: {result['invalid_at']}")
                print()
        except Exception as e:
            print(f"搜索失败: {e}")

    def do_demo(self, arg):
        """运行演示: demo"""
        try:
            from .main import demo
            asyncio.run(demo())
        except Exception as e:
            print(f"演示失败: {e}")

    def do_import_docs(self, arg):
        """导入文档到知识图谱: import_docs [directory]"""
        directory = arg.strip() or "dev_docs"

        print(f"📚 开始导入文档目录: {directory}")

        try:
            result = asyncio.run(import_docs_cli(directory))
            if result:
                print(f"✅ 导入完成！")
                print(f"   成功导入: {result['imported']} 个文件")
                print(f"   导入失败: {result['errors']} 个文件")
            else:
                print("❌ 导入失败，目录不存在或发生错误")
        except Exception as e:
            print(f"❌ 导入过程中发生错误: {e}")

    def do_list_docs(self, arg):
        """列出已导入的文档: list_docs [category_filter]"""
        category_filter = arg.strip() or None

        try:
            list_imported_docs_sync(category_filter)
        except Exception as e:
            print(f"❌ 列出文档时发生错误: {e}")

    def do_info(self, arg):
        """显示系统信息: info"""
        from .config import settings
        print("🖥️  Thera 系统信息")
        print(f"模型: {settings.llm_model}")
        print(f"API URL: {settings.llm_base_url}")
        print(f"Neo4j 数据库: {settings.neo4j_database}@{settings.neo4j_uri}")
        print(f"嵌入模型: {settings.llm_embedding_model}")
        print(f"重排模型: {settings.llm_reranker_model}")

    def do_help(self, arg):
        """显示帮助信息"""
        super().do_help(arg)
        print("\n常用命令:")
        print("  chat <消息>     - 与 AI 智能对话")
        print("  add <标题> <内容> - 添加知识到图谱")
        print("  search <查询>   - 搜索知识图谱")
        print("  import_docs [dir] - 导入文档到图谱")
        print("  list_docs [filter] - 列出已导入文档")
        print("  demo           - 运行功能演示")
        print("  info           - 显示系统信息")
        print("  version        - 显示版本")
        print("  exit/quit      - 退出程序")


def start_cli():
    """启动交互式命令行界面"""
    try:
        TheraCLI().cmdloop()
    except KeyboardInterrupt:
        print("\n再见！")
        sys.exit(0)
