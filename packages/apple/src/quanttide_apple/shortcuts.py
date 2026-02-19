"""
Shortcuts CLI 封装

提供 Shortcuts 命令行的 Python 封装，用于运行和管理 macOS Shortcuts。
"""

import subprocess
from pathlib import Path
from typing import Any, List, Optional


def list_shortcuts() -> List[str]:
    """列出所有可用的 Shortcuts"""
    try:
        result = subprocess.run(
            ["shortcuts", "list"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            return []
        shortcuts = result.stdout.strip().split("\n")
        return [s.strip() for s in shortcuts if s.strip()]
    except Exception:
        return []


def run_shortcut(
    name: str,
    input_data: Any = None,
    input_path: Path = None,
    output_path: Path = None,
    timeout: int = 120,
) -> Optional[str]:
    """
    运行指定的 Shortcut

    Args:
        name: Shortcut 名称
        input_data: 输入数据（将传递给 Shortcut）
        input_path: 输入文件路径（-i 参数）
        output_path: 输出文件路径（-o 参数）
        timeout: 超时时间（秒）

    Returns:
        Shortcut 的输出文本，失败返回 None
    """
    args = ["shortcuts", "run", name]

    if input_path:
        args.extend(["-i", str(input_path)])
    elif input_data:
        args.extend(["-i", "-"])  # 从 stdin 读取

    if output_path:
        args.extend(["-o", str(output_path)])

    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            input=input_data if input_data and not input_path else None,
            timeout=timeout,
        )
        if result.returncode != 0:
            return None
        return result.stdout
    except Exception:
        return None


def find_shortcut(pattern: str) -> Optional[str]:
    """
    模糊匹配 Shortcut 名称

    Args:
        pattern: 搜索模式（不区分大小写）

    Returns:
        匹配的 Shortcut 名称，未找到返回 None
    """
    shortcuts = list_shortcuts()
    pattern_lower = pattern.lower()

    for shortcut in shortcuts:
        if pattern_lower in shortcut.lower():
            return shortcut

    return None


def get_shortcut_info(name: str) -> Optional[dict]:
    """
    获取 Shortcut 详细信息（通过 AppleScript）

    Args:
        name: Shortcut 名称

    Returns:
        包含 Shortcut 信息的字典
    """
    script = f'''
    tell application "Shortcuts"
        set shortcutName to "{name}"
        try
            set shortcutData to shortcut shortcutName
            return name of shortcutData
        on error
            return ""
        end try
    end tell
    '''
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode == 0 and result.stdout.strip():
            return {"name": result.stdout.strip()}
    except Exception:
        pass
    return None
