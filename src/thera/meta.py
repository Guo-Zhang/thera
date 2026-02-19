"""
系统元信息模块

用于观察和描述系统自身的状态和属性
"""

import os
from pathlib import Path
from datetime import datetime
from typing import Any


DATA_DIR = Path(__file__).parent.parent.parent / "data"


def get_data_info() -> dict[str, Any]:
    """获取 data 文件夹信息"""
    if not DATA_DIR.exists():
        return {"exists": False, "path": str(DATA_DIR)}

    files = []
    total_size = 0

    for root, dirs, filenames in os.walk(DATA_DIR):
        for filename in filenames:
            filepath = Path(root) / filename
            stat = filepath.stat()
            files.append(
                {
                    "name": filename,
                    "path": str(filepath.relative_to(DATA_DIR)),
                    "size": stat.st_size,
                    "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                }
            )
            total_size += stat.st_size

    return {
        "exists": True,
        "path": str(DATA_DIR),
        "file_count": len(files),
        "total_size": total_size,
        "files": files,
    }


def get_timestamp() -> str:
    """获取当前时间戳"""
    return datetime.now().isoformat()
