"""
状态管理 - 存储
"""

import json
import yaml
from pathlib import Path


class StorageState:
    """存储状态管理器，限制操作范围在 thera 文件夹内"""

    def __init__(self, base_path: Path):
        self._base_path = base_path
        self._validate_path(base_path)
        self.base_path = base_path

    def _validate_path(self, path: Path):
        """验证路径是否在 thera 文件夹内"""
        if not str(path).startswith(str(self._base_path)):
            raise ValueError(f"Path {path} is outside thera folder")

    @property
    def allowed_paths(self) -> list[str]:
        """允许访问的路径列表"""
        return [str(self.base_path)]

    def ensure_dirs(self, *paths: str):
        """确保目录存在"""
        for p in paths:
            full_path = self._base_path / p
            self._validate_path(full_path)
            full_path.mkdir(parents=True, exist_ok=True)

    def get_data_dir(self, category: str) -> Path:
        """获取数据目录"""
        path = self.base_path / category
        self._validate_path(path)
        path.mkdir(parents=True, exist_ok=True)
        return path

    def save_json(self, category: str, filename: str, data: dict):
        """保存 JSON 文件"""
        path = self.get_data_dir(category) / filename
        self._validate_path(path)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_json(self, category: str, filename: str) -> dict | None:
        """加载 JSON 文件"""
        path = self.get_data_dir(category) / filename
        self._validate_path(path)
        if not path.exists():
            return None
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    def save_yaml(self, category: str, filename: str, data: dict):
        """保存 YAML 文件"""
        path = self.get_data_dir(category) / filename
        self._validate_path(path)
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, allow_unicode=True)

    def load_yaml(self, category: str, filename: str) -> dict | None:
        """加载 YAML 文件"""
        path = self.get_data_dir(category) / filename
        self._validate_path(path)
        if not path.exists():
            return None
        with open(path, encoding="utf-8") as f:
            return yaml.safe_load(f)
