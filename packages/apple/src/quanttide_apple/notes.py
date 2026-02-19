"""
Apple Notes 适配器

提供 Apple Notes（备忘录）的数据读取功能。
"""

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from .base import AppleAdapter, AppleResult, build_folder_tree


class NotesAdapter(AppleAdapter):
    """Apple Notes 备忘录适配器"""

    @property
    def app_name(self) -> str:
        return "Notes"

    def fetch(self, folder: str = None, limit: int = None) -> List[Dict[str, Any]]:
        """
        获取备忘录

        Args:
            folder: 文件夹名称，默认获取"思考"文件夹
            limit: 限制数量

        Returns:
            备忘录列表，每条包含 title 和 body
        """
        if folder:
            return self._get_notes_from_folder(folder)
        elif limit:
            return self._get_notes_by_limit(limit)
        else:
            return self._get_notes_from_folder("思考")

    def get_folder_structure(self) -> List[Dict[str, Any]]:
        """
        获取备忘录文件夹结构

        Returns:
            文件夹列表，每条包含 id, name, parent_id, note_count
        """
        return self._get_folder_structure()

    def get_note_names(self, limit: int = 10) -> List[str]:
        """
        获取备忘录标题列表

        Args:
            limit: 限制数量

        Returns:
            标题列表
        """
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

    def export(
        self,
        folder: str = "思考",
        output_path: Path = None,
        shortcut_name: str = "GetAllNotes",
    ) -> Dict[str, Any]:
        """
        导出备忘录到 JSON 文件

        Args:
            folder: 文件夹名称
            output_path: 输出路径，默认到当前目录
            shortcut_name: 使用的 Shortcut 名称

        Returns:
            导出结果字典
        """
        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            output_path = Path.cwd() / "notes.json"

        notes = []

        json_output = self.run_shortcut(shortcut_name)
        if json_output:
            try:
                data = json.loads(json_output)
                if isinstance(data, list):
                    notes = data
            except json.JSONDecodeError:
                pass

        if not notes:
            notes = self._get_notes_from_folder(folder)

        if not notes:
            names = self.get_note_names()
            notes = [{"title": name, "body": ""} for name in names]

        result = {
            "export_date": datetime.now().isoformat(),
            "total_count": len(notes),
            "notes": notes,
        }

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        return result

    def _get_notes_from_folder(self, folder_name: str) -> List[Dict[str, Any]]:
        """获取指定文件夹的备忘录"""
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

    def _get_notes_by_limit(self, limit: int) -> List[Dict[str, Any]]:
        """按限制获取备忘录"""
        script_lines = [
            'tell application "Notes"',
            f"set n to notes 1 thru {limit}",
            "set noteData to {}",
            "repeat with x in n",
            'set noteText to "###" & name of x & "###" & plaintext of x',
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

    def _get_folder_structure(self) -> List[Dict[str, Any]]:
        """获取文件夹结构"""
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
    """
    获取指定文件夹的备忘录（便捷函数）

    Args:
        folder_name: 文件夹名称

    Returns:
        备忘录列表
    """
    adapter = NotesAdapter()
    return adapter.fetch(folder=folder_name)


def get_note_names(limit: int = 10) -> List[str]:
    """
    获取备忘录标题列表（便捷函数）

    Args:
        limit: 限制数量

    Returns:
        标题列表
    """
    adapter = NotesAdapter()
    return adapter.get_note_names(limit=limit)


def export_notes(
    folder: str = "思考",
    output_path: Path = None,
    shortcut_name: str = "GetAllNotes",
) -> Dict[str, Any]:
    """
    导出备忘录到 JSON 文件（便捷函数）

    Args:
        folder: 文件夹名称
        output_path: 输出路径
        shortcut_name: 使用的 Shortcut 名称

    Returns:
        导出结果字典
    """
    adapter = NotesAdapter()
    return adapter.export(
        folder=folder, output_path=output_path, shortcut_name=shortcut_name
    )
