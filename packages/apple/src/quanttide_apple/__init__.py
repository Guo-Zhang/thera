"""
quanttide-apple - Apple ecosystem Python SDK

提供基于 Shortcuts 的 Apple 生态集成，包括 Notes, Contacts, Calendar, Reminders 等应用的数据访问。
"""

from .base import AppleAdapter, AppleResult
from .notes import NotesAdapter, get_notes_from_folder, get_note_names, export_notes
from .shortcuts import list_shortcuts, run_shortcut, find_shortcut

__all__ = [
    "AppleAdapter",
    "AppleResult",
    "NotesAdapter",
    "list_shortcuts",
    "run_shortcut",
    "find_shortcut",
    "get_notes_from_folder",
    "get_note_names",
    "export_notes",
]

__version__ = "0.1.0"
