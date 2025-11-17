"""
文档导入器模块

用于将文档文件导入到 Graphiti 知识图谱中。
"""

import os
import asyncio
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

from .main import Thera
from .config import settings


class DocsImporter:
    """文档导入器类，用于将文档内容导入知识图谱"""

    def __init__(self, thera: Thera = None):
        self.thera = thera or Thera()
        self.initialized = False

    async def initialize(self):
        """初始化导入器"""
        if not self.initialized:
            await self.thera.initialize()
            self.initialized = True

    async def import_markdown_file(self, file_path: Path, category: str = "documentation"):
        """导入单个 Markdown 文件到知识图谱"""
        await self.initialize()

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # 提取文件名作为知识标题
            title = file_path.stem

            # 构建知识内容，包含文件路径信息
            try:
                source_description = f"文档导入: {file_path.relative_to(Path.cwd())}"
            except ValueError:
                # 如果文件不在当前目录下，使用完整路径
                source_description = f"文档导入: {file_path}"

            # 添加分类标签
            knowledge_content = f"""分类: {category}
文件: {file_path.name}

{content}
"""

            success = await self.thera.add_knowledge(
                name=title,
                content=knowledge_content,
                source=source_description
            )

            if success:
                print(f"✅ 已导入: {file_path.name}")
                return True
            else:
                print(f"❌ 导入失败: {file_path.name}")
                return False

        except Exception as e:
            print(f"❌ 导入错误 {file_path.name}: {e}")
            return False

    async def import_directory(self, dir_path: Path, recursive: bool = True):
        """导入整个目录的文档"""
        await self.initialize()

        imported_count = 0
        error_count = 0

        # 遍历目录中的所有 Markdown 文件
        pattern = "**/*.md" if recursive else "*.md"

        for md_file in dir_path.glob(pattern):
            # 使用相对路径作为分类
            relative_path = md_file.relative_to(dir_path)
            category = str(relative_path.parent) if relative_path.parent.name else "root"

            if await self.import_markdown_file(md_file, category):
                imported_count += 1
            else:
                error_count += 1

        return {
            'imported': imported_count,
            'errors': error_count,
            'total': imported_count + error_count
        }

    async def import_dev_docs(self):
        """专门导入 dev_docs 目录的文档"""
        dev_docs_path = Path("dev_docs")

        if not dev_docs_path.exists():
            print("❌ dev_docs 目录不存在")
            return None

        print(f"🔍 开始导入 dev_docs 文档...")
        print(f"目录位置: {dev_docs_path.absolute()}")

        result = await self.import_directory(dev_docs_path)

        print(f"\n📊 导入完成:")
        print(f"✅ 成功导入: {result['imported']}")
        print(f"❌ 导入失败: {result['errors']}")
        print(f"📋 总计文件: {result['total']}")

        return result

    async def list_imported_docs(self, category_filter: str = None):
        """列出已导入的文档"""
        await self.initialize()

        query = "文档导入"
        if category_filter:
            query += f" {category_filter}"

        results = await self.thera.search_knowledge(query)

        print(f"🔍 找到 {len(results)} 条相关记录:")
        for i, result in enumerate(results, 1):
            fact = result['fact']
            # 提取标题和分类信息
            lines = fact.split('\n')
            title = "未知标题"
            file_info = "未知文件"

            for line in lines:
                if line.startswith('分类:'):
                    category = line.replace('分类:', '').strip()
                elif line.startswith('文件:'):
                    file_info = line.replace('文件:', '').strip()
                elif not line.startswith('分类:') and not line.startswith('文件:') and line.strip():
                    if title == "未知标题":
                        title = line.strip()

            print(f"{i}. {title}")
            print(f"   文件: {file_info}")
            print(f"   分类: {category}")
            print()

    async def close(self):
        """关闭导入器"""
        if self.initialized:
            await self.thera.close()

    async def __aenter__(self):
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()


# 便捷的同步函数包装器
def import_dev_docs_sync():
    """同步版本的导入 dev_docs 函数"""
    importer = DocsImporter()
    return asyncio.run(importer.import_dev_docs())


def list_imported_docs_sync(category_filter: str = None):
    """同步版本的列出已导入文档函数"""
    importer = DocsImporter()
    return asyncio.run(importer.list_imported_docs(category_filter))


# CLI 命令函数
async def import_docs_cli(directory: str = "dev_docs"):
    """CLI 版本的导入函数"""
    async with DocsImporter() as importer:
        if directory == "dev_docs":
            return await importer.import_dev_docs()
        else:
            path = Path(directory)
            if not path.exists():
                print(f"❌ 目录不存在: {directory}")
                return None
            return await importer.import_directory(path)


if __name__ == "__main__":
    # 运行演示导入
    async def demo():
        print("📚 DocsImporter 演示")
        print("=" * 50)

        async with DocsImporter() as importer:
            # 导入 dev_docs
            result = await importer.import_dev_docs()

            if result:
                print("\n📋 列出已导入文档:")
                await importer.list_imported_docs()

    asyncio.run(demo())