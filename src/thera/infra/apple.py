"""
苹果备忘录

功能：导入本地苹果备忘录数据，存入项目数据目录的`/infra/apple` 文件夹。

实现方案：使用 AppleScript 读取本地备忘录数据
- 通过 osascript 调用系统 AppleScript
- 支持获取指定文件夹的备忘录（如"思考"文件夹）
- 支持通过 Shortcut 获取完整备忘录数据
- 也支持手动导入 JSON 文件
- 导出为 JSON 格式存储到 data/infra/apple/
"""

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


def get_notes_folder_structure() -> List[Dict[str, Any]]:
    """获取备忘录文件夹元数据（含父级关系与条目数量）"""
    script_lines = [
        'tell application "Notes"',
        "set folderData to {}",
        "repeat with f in every folder",
        "set folderId to (id of f) as string",
        "set folderName to name of f",
        "set noteCount to count of notes in f",
        'set parentId to ""',
        "try",
        "set parentRef to container of f",
        "if class of parentRef is folder then",
        "set parentId to (id of parentRef) as string",
        "end if",
        "end try",
        'set folderText to folderId & "|||" & folderName & "|||" & parentId & "|||" & (noteCount as string)',
        "set end of folderData to folderText",
        "end repeat",
        "set oldDelims to AppleScript's text item delimiters",
        "set AppleScript's text item delimiters to linefeed",
        "set outputText to folderData as text",
        "set AppleScript's text item delimiters to oldDelims",
        "return outputText",
        "end tell",
    ]
    args = ["osascript"]
    for line in script_lines:
        args.extend(["-e", line])
    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode != 0:
            return []

        output = result.stdout.strip()
        if not output:
            return []

        folders = []
        for item in output.splitlines():
            parts = item.split("|||", 3)
            if len(parts) != 4:
                continue
            folder_id, name, parent_id, count_text = parts
            folder_id = folder_id.strip()
            name = name.strip()
            parent_id = parent_id.strip() or None
            count_text = count_text.strip()
            if not folder_id or not name:
                continue
            try:
                note_count = int(count_text)
            except ValueError:
                note_count = 0
            folders.append(
                {
                    "id": folder_id,
                    "name": name,
                    "parent_id": parent_id,
                    "note_count": note_count,
                }
            )
        return folders
    except Exception:
        return []


def get_notes_from_folder(folder_name: str = "思考") -> List[Dict[str, Any]]:
    """获取指定文件夹的备忘录（包含标题和内容）"""
    script_lines = [
        'tell application "Notes"',
        "set noteData to {}",
        f'set targetFolder to folder "{folder_name}"',
        "repeat with n in every note in targetFolder",
        "set noteTitle to name of n",
        "set noteBody to plaintext of n",
        'set noteText to "###" & noteTitle & "###" & noteBody',
        "set end of noteData to noteText",
        "end repeat",
        "return noteData",
        "end tell",
    ]
    args = ["osascript"]
    for line in script_lines:
        args.extend(["-e", line])
    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=180,
        )
        if result.returncode != 0:
            return []

        output = result.stdout.strip()
        if not output:
            return []

        notes = []
        items = output.split(", ###")
        for item in items:
            if "###" in item:
                parts = item.split("###", 1)
                if len(parts) == 2:
                    title, body = parts
                    title = title.strip()
                    if title:
                        notes.append({"title": title, "body": body.strip()})

        return notes
    except Exception:
        return []

        output = result.stdout.strip()
        if not output:
            return []

        notes = []
        for item in output.split(", "):
            if "###" in item:
                parts = item.split("###", 1)
                if len(parts) == 2:
                    title, body = parts
                    notes.append({"title": title.strip(), "body": body.strip()})

        return notes
    except Exception:
        return []

        output = result.stdout.strip()
        if not output:
            return []

        notes = []
        current_note = {}
        for line in output.split("\n"):
            if line.startswith("title:"):
                if current_note:
                    notes.append(current_note)
                title = line.replace("title:", "").strip()
                title = title.strip('"')
                current_note = {"title": title, "body": ""}
            elif line.startswith("body:"):
                body = line.replace("body:", "").strip()
                body = body.strip('"')
                current_note["body"] = body

        if current_note:
            notes.append(current_note)

        return notes
    except Exception:
        return []


def get_note_names(limit: int = 10) -> List[str]:
    """获取备忘录标题（默认获取前100条）"""
    script_lines = [
        'tell application "Notes"',
        f"set n to notes 1 thru {limit}",
        "set names to {}",
        "repeat with x in n",
        "set end of names to name of x",
        "end repeat",
        "return names",
        "end tell",
    ]
    args = ["osascript"]
    for line in script_lines:
        args.extend(["-e", line])
    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode != 0:
            return []
        names = result.stdout.strip().split(", ")
        return [n.strip() for n in names if n.strip()]
    except Exception:
        return []


def run_shortcut(shortcut_name: str = "GetAllNotes") -> Optional[str]:
    """运行 Shortcut 获取备忘录"""
    try:
        result = subprocess.run(
            ["shortcuts", "run", shortcut_name],
            capture_output=True,
            text=True,
            timeout=120,
        )
        if result.returncode != 0:
            return None
        return result.stdout
    except Exception:
        return None


def export_notes(output_dir: Path, folder_name: str = "思考") -> Dict[str, Any]:
    """导出备忘录到 JSON 文件（默认获取"思考"文件夹）"""
    output_dir.mkdir(parents=True, exist_ok=True)

    notes = []

    json_output = run_shortcut()
    if json_output:
        try:
            data = json.loads(json_output)
            if isinstance(data, list):
                notes = data
        except json.JSONDecodeError:
            pass

    if not notes:
        notes = get_notes_from_folder(folder_name)

    if not notes:
        names = get_note_names()
        notes = [{"title": name, "body": ""} for name in names]

    result = {
        "export_date": datetime.now().isoformat(),
        "total_count": len(notes),
        "notes": notes,
    }

    output_file = output_dir / "notes.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

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
    nodes: Dict[str, Dict[str, Any]] = {}
    for folder in folders:
        node = {
            "id": folder.get("id"),
            "name": folder.get("name"),
            "parent_id": folder.get("parent_id"),
            "note_count": folder.get("note_count", 0),
            "children": [],
        }
        folder_id = node["id"]
        if isinstance(folder_id, str) and folder_id:
            nodes[folder_id] = node

    roots: List[Dict[str, Any]] = []
    for node in nodes.values():
        parent_id = node.get("parent_id")
        if isinstance(parent_id, str) and parent_id in nodes:
            nodes[parent_id]["children"].append(node)
        else:
            roots.append(node)
    return roots


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
