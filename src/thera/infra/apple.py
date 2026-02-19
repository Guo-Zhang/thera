"""
苹果备忘录

功能：导入本地苹果备忘录数据，存入项目数据目录的`/infra/apple` 文件夹。

实现方案：
- 使用 quanttide_apple 包提供的 Shortcuts 和 Notes 适配器
- 也支持通过 Shortcut 获取完整备忘录数据
- 支持手动导入 JSON 文件
- 导出为 JSON 格式存储到 data/infra/apple/
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from quanttide_apple import NotesAdapter as _NotesAdapter
from quanttide_apple import run_shortcut as _run_shortcut
from quanttide_apple.base import build_folder_tree as _build_folder_tree


_notes_adapter = _NotesAdapter()


def get_notes_folder_structure() -> List[Dict[str, Any]]:
    """获取备忘录文件夹元数据（含父级关系与条目数量）"""
    return _notes_adapter.get_folder_structure()


def get_notes_from_folder(folder_name: str = "思考") -> List[Dict[str, Any]]:
    """获取指定文件夹的备忘录（包含标题和内容）"""
    return _notes_adapter.fetch(folder=folder_name)


def get_note_names(limit: int = 10) -> List[str]:
    """获取备忘录标题（默认获取前10条）"""
    return _notes_adapter.get_note_names(limit=limit)


def run_shortcut(shortcut_name: str = "GetAllNotes") -> Optional[str]:
    """运行 Shortcut 获取备忘录"""
    return _run_shortcut(shortcut_name)


def export_notes(output_dir: Path, folder_name: str = "思考") -> Dict[str, Any]:
    """导出备忘录到 JSON 文件（默认获取"思考"文件夹）"""
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / "notes.json"

    adapter = _NotesAdapter()
    result = adapter.export(folder=folder_name, output_path=output_file)

    return result


def import_notes(input_file: Path, output_dir: Path) -> Dict[str, Any]:
    """从 JSON 文件导入备忘录"""
    output_dir.mkdir(parents=True, exist_ok=True)

    with open(input_file, encoding="utf-8") as f:
        data = json.load(f)

    notes = data.get("notes", []) if isinstance(data, dict) else data

    result = {
        "import_date": datetime.now().isoformat(),
        "total_count": len(notes),
        "notes": notes,
    }

    output_file = output_dir / "notes.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    return result


def list_notes(output_dir: Path) -> List[Dict[str, Any]]:
    """列出已导出的备忘录"""
    notes_file = output_dir / "notes.json"
    if not notes_file.exists():
        return []
    with open(notes_file, encoding="utf-8") as f:
        data = json.load(f)
    return [{"title": n.get("title")} for n in data.get("notes", [])]


def get_note_by_title(output_dir: Path, title: str) -> Optional[Dict[str, Any]]:
    """根据标题获取备忘录"""
    notes_file = output_dir / "notes.json"
    if not notes_file.exists():
        return None
    with open(notes_file, encoding="utf-8") as f:
        data = json.load(f)
    for note in data.get("notes", []):
        if note.get("title") == title:
            return note
    return None


def search_notes(output_dir: Path, keyword: str) -> List[Dict[str, Any]]:
    """搜索备忘录"""
    notes_file = output_dir / "notes.json"
    if not notes_file.exists():
        return []
    with open(notes_file, encoding="utf-8") as f:
        data = json.load(f)

    keyword = keyword.lower()
    return [
        n
        for n in data.get("notes", [])
        if keyword in n.get("title", "").lower() or keyword in n.get("body", "").lower()
    ]


def get_default_output_dir() -> Path:
    """获取默认输出目录"""
    return Path(__file__).parent.parent.parent.parent / "data" / "infra" / "apple"


def build_folder_tree(folders: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """将扁平文件夹列表转换为树结构"""
    return _build_folder_tree(folders)


def export_folder_structure(output_dir: Path) -> Dict[str, Any]:
    """导出备忘录文件夹结构到 JSON 文件"""
    output_dir.mkdir(parents=True, exist_ok=True)
    folders = get_notes_folder_structure()
    tree = build_folder_tree(folders)
    result = {
        "export_date": datetime.now().isoformat(),
        "total_count": len(folders),
        "folders": tree,
    }
    output_file = output_dir / "folder_structure.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    return result


def main():
    """主函数：导出备忘录文件夹结构"""
    output_dir = get_default_output_dir()
    result = export_folder_structure(output_dir)
    output_file = output_dir / "folder_structure.json"
    print(f"已导出备忘录文件夹结构到: {output_file}")
    print(f"文件夹数量: {result['total_count']}")
    for folder in result["folders"][:10]:
        print(f"  - {folder.get('name')} ({folder.get('note_count')} 条)")
    if result["total_count"] > 10:
        print(f"  ... 共 {result['total_count']} 个文件夹")
    return 0


if __name__ == "__main__":
    exit(main())
