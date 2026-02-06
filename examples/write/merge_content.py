"""
合并片段和正文到一个Markdown文件
"""

from pathlib import Path
import yaml

# 读取 TOC
toc_path = Path('data/storage/jupyterbook/_toc.yml')
with open(toc_path, 'r', encoding='utf-8') as f:
    toc = yaml.safe_load(f)

jupyterbook_path = Path('data/storage/jupyterbook')
output_path = Path('data/storage/write_analysis/merged_content.md')

# 分类文档
fragments = []
main_texts = []

current_part = None
for item in toc:
    if isinstance(item, dict) and 'part' in item:
        current_part = item['part']
        if current_part == '片段' and 'chapters' in item:
            for chapter in item['chapters']:
                fragments.append(chapter.get('file', ''))
        elif current_part == '正文' and 'chapters' in item:
            for chapter in item['chapters']:
                main_texts.append(chapter.get('file', ''))

print(f"找到片段文件: {fragments}")
print(f"找到正文文件: {main_texts}")

# 写入 Markdown
with open(output_path, 'w', encoding='utf-8') as f:
    f.write('# 片段与正文合集\n\n')
    f.write('本文档由飞书知识库自动生成。\n\n')
    
    # 片段部分
    f.write('---\n\n# 片段\n\n')
    for fragment_file in fragments:
        if fragment_file:
            # 添加 .md 扩展名
            if not fragment_file.endswith('.md'):
                fragment_file = fragment_file + '.md'
            md_file = jupyterbook_path / fragment_file
            print(f"读取片段: {md_file}, 存在: {md_file.exists()}")
            if md_file.exists():
                with open(md_file, 'r', encoding='utf-8') as f_in:
                    content = f_in.read()
                f.write(content)
                f.write('\n\n---\n\n')
    
    # 正文部分
    f.write('# 正文\n\n')
    for main_file in main_texts:
        if main_file:
            # 添加 .md 扩展名
            if not main_file.endswith('.md'):
                main_file = main_file + '.md'
            md_file = jupyterbook_path / main_file
            print(f"读取正文: {md_file}, 存在: {md_file.exists()}")
            if md_file.exists():
                with open(md_file, 'r', encoding='utf-8') as f_in:
                    content = f_in.read()
                f.write(content)
                f.write('\n\n---\n\n')

print(f'\n合并完成，输出文件: {output_path}')
print(f'片段数量: {len(fragments)}')
print(f'正文数量: {len(main_texts)}')
