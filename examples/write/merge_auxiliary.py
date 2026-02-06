"""
合并辅助内容（原型、设定、剧情、风格）到一个Markdown文件
"""

from pathlib import Path
import yaml

# 读取 TOC
toc_path = Path('data/storage/jupyterbook/_toc.yml')
with open(toc_path, 'r', encoding='utf-8') as f:
    toc = yaml.safe_load(f)

jupyterbook_path = Path('data/storage/jupyterbook')
output_path = Path('data/storage/write_analysis/auxiliary_content.md')

# 获取所有 .md 文件，建立映射表
md_files = {}
for md_file in jupyterbook_path.glob('*.md'):
    name = md_file.stem
    md_files[name] = md_file

# 分类辅助内容
auxiliary_sections = {
    '原型': [],
    '设定': [],
    '剧情': [],
    '风格': [],
    '其他': []
}

current_part = None
for item in toc:
    if isinstance(item, dict) and 'part' in item:
        current_part = item['part']
        # 移除冒号后缀
        current_part_clean = current_part.split('：')[0]
        if current_part_clean in auxiliary_sections and 'chapters' in item:
            for chapter in item['chapters']:
                chapter_name = chapter.get('file', '')
                if chapter_name:
                    # 移除冒号后的部分作为key
                    key = chapter_name.split('：')[-1]
                    auxiliary_sections[current_part_clean].append(key)
    elif isinstance(item, dict) and 'file' in item:
        # 独立的文件
        file_name = item['file']
        if file_name not in ['片段', '正文']:
            # 移除冒号后的部分作为key
            key = file_name.split('：')[-1]
            auxiliary_sections['其他'].append(key)

print("找到的辅助文件:")
for section, files in auxiliary_sections.items():
    print(f"  {section}: {files}")

# 写入 Markdown
with open(output_path, 'w', encoding='utf-8') as f:
    f.write('# 辅助内容合集\n\n')
    f.write('本文档包含原型、设定、剧情、风格等辅助内容，由飞书知识库自动生成。\n\n')

    # 其他部分
    if auxiliary_sections['其他']:
        f.write('---\n\n# 其他\n\n')
        for key in auxiliary_sections['其他']:
            # 查找匹配的文件
            for md_file in md_files.values():
                if key in md_file.stem:
                    print(f"读取其他文件: {md_file}")
                    with open(md_file, 'r', encoding='utf-8') as f_in:
                        content = f_in.read()
                    f.write(content)
                    f.write('\n\n---\n\n')
                    break

    # 原型部分
    if auxiliary_sections['原型']:
        f.write('# 原型：情感考古与叙事重构\n\n')
        for key in auxiliary_sections['原型']:
            for md_file in md_files.values():
                if key in md_file.stem:
                    print(f"读取原型文件: {md_file}")
                    with open(md_file, 'r', encoding='utf-8') as f_in:
                        content = f_in.read()
                    f.write(content)
                    f.write('\n\n---\n\n')
                    break

    # 设定部分
    if auxiliary_sections['设定']:
        f.write('# 设定\n\n')
        for key in auxiliary_sections['设定']:
            for md_file in md_files.values():
                if key in md_file.stem:
                    print(f"读取设定文件: {md_file}")
                    with open(md_file, 'r', encoding='utf-8') as f_in:
                        content = f_in.read()
                    f.write(content)
                    f.write('\n\n---\n\n')
                    break

    # 剧情部分
    if auxiliary_sections['剧情']:
        f.write('# 剧情：双向暗恋的久别重逢\n\n')
        for key in auxiliary_sections['剧情']:
            for md_file in md_files.values():
                if key in md_file.stem:
                    print(f"读取剧情文件: {md_file}")
                    with open(md_file, 'r', encoding='utf-8') as f_in:
                        content = f_in.read()
                    f.write(content)
                    f.write('\n\n---\n\n')
                    break

    # 风格部分
    if auxiliary_sections['风格']:
        f.write('# 风格：中西合璧的现代美\n\n')
        for key in auxiliary_sections['风格']:
            for md_file in md_files.values():
                if key in md_file.stem:
                    print(f"读取风格文件: {md_file}")
                    with open(md_file, 'r', encoding='utf-8') as f_in:
                        content = f_in.read()
                    f.write(content)
                    f.write('\n\n---\n\n')
                    break

print(f'\n合并完成，输出文件: {output_path}')
for section, files in auxiliary_sections.items():
    print(f'{section}: {len(files)} 个文件')
