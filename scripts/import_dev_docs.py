#!/usr/bin/env python3
"""
dev_docs 导入脚本

用于将 dev_docs 目录的文档导入到 Graphiti 知识图谱中。
"""

import asyncio
import sys
from pathlib import Path

# 添加 src 目录到路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

from thera.docs_importer import DocsImporter


async def main():
    """主函数"""
    print("📚 Thera dev_docs 导入工具")
    print("=" * 50)

    # 检查 dev_docs 目录是否存在
    dev_docs_path = Path("dev_docs")
    if not dev_docs_path.exists():
        print("❌ 错误: dev_docs 目录不存在")
        print("请确保在当前目录下有 dev_docs 文件夹")
        return

    # 列出将要导入的文件
    md_files = list(dev_docs_path.glob("**/*.md"))
    if not md_files:
        print("⚠️  警告: 在 dev_docs 目录中未找到任何 .md 文件")
        return

    print(f"📋 发现 {len(md_files)} 个 Markdown 文件:")
    for md_file in md_files:
        print(f"  • {md_file.relative_to(dev_docs_path)}")

    print("\n🔍 检查环境配置...")
    from thera.config import settings

    # 检查必要的环境变量
    required_vars = [
        'llm_api_key',
        'neo4j_uri',
        'neo4j_user',
        'neo4j_password'
    ]

    missing_vars = []
    for var in required_vars:
        if not getattr(settings, var, None):
            missing_vars.append(var)

    if missing_vars:
        print("❌ 缺少必要的环境变量:")
        for var in missing_vars:
            print(f"  - {var.upper()}")
        print("\n请在 .env 文件中配置这些变量")
        return

    print("✅ 环境配置检查通过")
    print(f"  LLM API: {settings.llm_base_url}")
    print(f"  Neo4j: {settings.neo4j_database}@{settings.neo4j_uri}")

    # 确认操作（在非交互式环境中自动继续）
    print("\n⏳ 准备导入文档到知识图谱...")

    # 如果是非交互式环境，自动继续
    if not sys.stdin.isatty():
        print("非交互式环境，自动继续导入...")
    else:
        response = input("是否继续? (y/N): ").strip().lower()
        if response not in ['y', 'yes']:
            print("操作已取消")
            return

    # 执行导入
    print("\n🚀 开始导入...")
    print("这可能需要几分钟时间，具体取决于文档数量。")

    try:
        async with DocsImporter() as importer:
            result = await importer.import_dev_docs()

            if result:
                print("\n🎉 导入完成！")
                print("=" * 50)

                if result['imported'] > 0:
                    print(f"✅ 成功导入: {result['imported']} 个文件")

                    # 询问是否列出已导入的文档
                    list_response = input("\n是否列出已导入的文档? (y/N): ").strip().lower()
                    if list_response in ['y', 'yes']:
                        print("\n📋 已导入的文档列表:")
                        await importer.list_imported_docs()

                if result['errors'] > 0:
                    print(f"⚠️  导入失败: {result['errors']} 个文件")

                print(f"📊 总计处理: {result['total']} 个文件")

                print("\n💡 现在你可以使用以下命令查询导入的知识:")
                print("  thera search '知识工程'")
                print("  thera chat '关于开发者工具有哪些建议'")
            else:
                print("❌ 导入失败")

    except KeyboardInterrupt:
        print("\n\n⚠️  导入被用户中断")
    except Exception as e:
        print(f"\n❌ 导入过程中发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())