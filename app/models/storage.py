from pathlib import Path
from typing import Dict, List, Optional, Callable
import os
from app.utils.encryption import EncryptionManager
from app.models.password_entry import PasswordEntry, PasswordCategory


class StorageManager:
    """密码存储管理器，处理加密存储和检索"""
    
    def __init__(self, encryption_manager: EncryptionManager, storage_file: Path):
        """
        初始化存储管理器
        :param encryption_manager: 加密管理器实例
        :param storage_file: 加密存储文件路径
        """
        self.encryption_manager = encryption_manager
        self.storage_file = storage_file
        self._cache: Optional[Dict[str, PasswordEntry]] = None
    
    def _load_from_file(self) -> Dict[str, PasswordEntry]:
        """从加密文件加载所有密码条目"""
        if not self.encryption_manager.is_unlocked():
            raise RuntimeError("密码本未解锁")
        
        if not self.storage_file.exists():
            return {}
        
        try:
            raw_data = self.encryption_manager.decrypt_from_file(self.storage_file)
            if raw_data is None:
                return {}
            
            result = {}
            for entry_id, entry_data in raw_data.items():
                result[entry_id] = PasswordEntry.from_dict(entry_data)
            return result
        except Exception:
            return {}
    
    def _save_to_file(self, entries: Dict[str, PasswordEntry]) -> None:
        """将所有密码条目加密保存到文件"""
        if not self.encryption_manager.is_unlocked():
            raise RuntimeError("密码本未解锁")
        
        raw_data = {}
        for entry_id, entry in entries.items():
            raw_data[entry_id] = entry.to_dict()
        
        self.encryption_manager.encrypt_to_file(raw_data, self.storage_file)
        self._cache = entries.copy()
    
    def add_entry(self, entry: PasswordEntry) -> bool:
        """
        添加新的密码条目
        :param entry: PasswordEntry 实例
        :return: 是否添加成功
        """
        entries = self._load_from_file()
        
        if entry.id in entries:
            return False
        
        entries[entry.id] = entry
        self._save_to_file(entries)
        return True
    
    def get_entry(self, entry_id: str) -> Optional[PasswordEntry]:
        """
        根据 ID 获取密码条目
        :param entry_id: 条目 ID
        :return: PasswordEntry 实例或 None
        """
        entries = self._load_from_file()
        return entries.get(entry_id)
    
    def get_all_entries(self) -> List[PasswordEntry]:
        """
        获取所有密码条目
        :return: PasswordEntry 列表，按更新时间降序排列
        """
        entries = self._load_from_file()
        result = list(entries.values())
        result.sort(key=lambda x: x.updated_at, reverse=True)
        return result
    
    def update_entry(self, entry_id: str, updated_data: dict) -> bool:
        """
        更新密码条目
        :param entry_id: 条目 ID
        :param updated_data: 更新的数据字典
        :return: 是否更新成功
        """
        entries = self._load_from_file()
        
        if entry_id not in entries:
            return False
        
        entry = entries[entry_id]
        
        if "title" in updated_data:
            entry.title = updated_data["title"]
        if "username" in updated_data:
            entry.username = updated_data["username"]
        if "password" in updated_data:
            entry.password = updated_data["password"]
        if "url" in updated_data:
            entry.url = updated_data["url"]
        if "category" in updated_data:
            category = updated_data["category"]
            if isinstance(category, str):
                try:
                    entry.category = PasswordCategory(category)
                except ValueError:
                    entry.category = PasswordCategory.OTHER
            else:
                entry.category = category
        if "notes" in updated_data:
            entry.notes = updated_data["notes"]
        
        entry.update_timestamp()
        entries[entry_id] = entry
        
        self._save_to_file(entries)
        return True
    
    def delete_entry(self, entry_id: str) -> bool:
        """
        删除密码条目
        :param entry_id: 条目 ID
        :return: 是否删除成功
        """
        entries = self._load_from_file()
        
        if entry_id not in entries:
            return False
        
        del entries[entry_id]
        self._save_to_file(entries)
        return True
    
    def search_entries(self, query: str) -> List[PasswordEntry]:
        """
        搜索密码条目
        :param query: 搜索关键词
        :return: 匹配的 PasswordEntry 列表
        """
        entries = self._load_from_file()
        result = []
        
        query_lower = query.lower()
        
        for entry in entries.values():
            if (
                query_lower in entry.title.lower()
                or query_lower in entry.username.lower()
                or query_lower in entry.notes.lower()
                or query_lower in entry.url.lower()
            ):
                result.append(entry)
        
        result.sort(key=lambda x: x.updated_at, reverse=True)
        return result
    
    def get_entries_by_category(self, category: PasswordCategory) -> List[PasswordEntry]:
        """
        按分类获取密码条目
        :param category: 分类枚举值
        :return: 该分类下的 PasswordEntry 列表
        """
        entries = self._load_from_file()
        
        target_category_value = None
        if isinstance(category, PasswordCategory):
            target_category_value = category.value
        elif isinstance(category, str):
            target_category_value = category
        
        if not isinstance(target_category_value, str):
            return []
        
        result = []
        for entry in entries.values():
            entry_category_value = None
            
            if isinstance(entry.category, PasswordCategory):
                entry_category_value = entry.category.value
            elif isinstance(entry.category, str):
                entry_category_value = entry.category
            elif hasattr(entry.category, 'value'):
                val = entry.category.value
                if isinstance(val, str):
                    entry_category_value = val
            
            if isinstance(entry_category_value, str) and entry_category_value == target_category_value:
                result.append(entry)
        
        result.sort(key=lambda x: x.updated_at, reverse=True)
        return result
    
    def get_categories_count(self) -> Dict[str, int]:
        """
        获取各分类的条目数量
        :return: 字典，键为分类名，值为数量
        """
        entries = self._load_from_file()
        counts = {cat.value: 0 for cat in PasswordCategory}
        
        for entry in entries.values():
            category_value = None
            
            if isinstance(entry.category, PasswordCategory):
                category_value = entry.category.value
            elif isinstance(entry.category, str):
                category_value = entry.category
            elif hasattr(entry.category, 'value'):
                val = entry.category.value
                if isinstance(val, str):
                    category_value = val
            elif isinstance(entry.category, dict):
                val = entry.category.get('value') or entry.category.get('name')
                if isinstance(val, str):
                    category_value = val
            
            if isinstance(category_value, str) and category_value in counts:
                counts[category_value] += 1
        
        return counts
    
    def is_empty(self) -> bool:
        """检查是否没有任何密码条目"""
        entries = self._load_from_file()
        return len(entries) == 0
    
    def get_total_count(self) -> int:
        """获取密码条目总数"""
        entries = self._load_from_file()
        return len(entries)
