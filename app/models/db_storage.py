from typing import Dict, List, Optional
import base64
import json
from datetime import datetime
from sqlalchemy.orm import Session

from app.utils.encryption import PasswordHasher, EncryptionManager
from app.models.password_entry import PasswordEntry, PasswordCategory
from app.models.database import MasterPassword, PasswordEntryDB


class DBEncryptionManager(EncryptionManager):
    """数据库版本的加密管理器，主密码信息存储在数据库中"""
    
    def __init__(self, db_session: Session, master_password: Optional[str] = None):
        """
        初始化加密管理器
        :param db_session: 数据库会话
        :param master_password: 用户主密码（可选，首次设置或验证时需要）
        """
        self.db_session = db_session
        self._fernet = None
        self._salt = None
        self._password_hash = None
        self._is_unlocked = False
    
    def is_master_password_set(self) -> bool:
        """检查是否已设置主密码"""
        result = self.db_session.query(MasterPassword).first()
        return result is not None
    
    def setup_master_password(self, password: str) -> bool:
        """
        首次设置主密码
        :param password: 用户选择的主密码
        :return: 是否成功
        """
        if self.is_master_password_set():
            return False
        
        hashed_password, salt = PasswordHasher.hash_password(password)
        
        fernet_key = PasswordHasher.password_to_fernet_key(password, salt)
        
        master_pw = MasterPassword(
            password_hash=base64.b64encode(hashed_password).decode('utf-8'),
            salt=base64.b64encode(salt).decode('utf-8')
        )
        self.db_session.add(master_pw)
        self.db_session.commit()
        
        self._salt = salt
        self._password_hash = hashed_password
        from cryptography.fernet import Fernet
        self._fernet = Fernet(fernet_key)
        self._is_unlocked = True
        
        return True
    
    def unlock(self, password: str) -> bool:
        """
        使用主密码解锁密码本
        :param password: 用户输入的主密码
        :return: 是否解锁成功
        """
        if not self.is_master_password_set():
            return False
        
        try:
            master_pw = self.db_session.query(MasterPassword).first()
            if master_pw is None:
                return False
            
            stored_salt = base64.b64decode(master_pw.salt)
            stored_hash = base64.b64decode(master_pw.password_hash)
            
            if not PasswordHasher.verify_password(password, stored_hash, stored_salt):
                return False
            
            fernet_key = PasswordHasher.password_to_fernet_key(password, stored_salt)
            from cryptography.fernet import Fernet
            
            self._salt = stored_salt
            self._password_hash = stored_hash
            self._fernet = Fernet(fernet_key)
            self._is_unlocked = True
            
            return True
            
        except Exception as e:
            print(f"Unlock error: {e}")
            return False


class DBStorageManager:
    """数据库版本的密码存储管理器"""
    
    def __init__(self, encryption_manager: DBEncryptionManager, db_session: Session):
        """
        初始化存储管理器
        :param encryption_manager: 加密管理器实例
        :param db_session: 数据库会话
        """
        self.encryption_manager = encryption_manager
        self.db_session = db_session
        self._cache: Optional[Dict[str, PasswordEntry]] = None
    
    def _load_from_db(self) -> Dict[str, PasswordEntry]:
        """从数据库加载所有密码条目"""
        if not self.encryption_manager.is_unlocked():
            raise RuntimeError("密码本未解锁")
        
        entries = self.db_session.query(PasswordEntryDB).all()
        
        result = {}
        for entry_db in entries:
            try:
                encrypted_data = base64.b64decode(entry_db.encrypted_data)
                raw_data = self.encryption_manager.decrypt(encrypted_data)
                entry = PasswordEntry.from_dict(raw_data)
                entry.created_at = entry_db.created_at
                entry.updated_at = entry_db.updated_at
                result[entry.id] = entry
            except Exception as e:
                print(f"Failed to load entry {entry_db.id}: {e}")
                continue
        
        return result
    
    def _save_to_db(self, entries: Dict[str, PasswordEntry]) -> None:
        """将所有密码条目保存到数据库"""
        if not self.encryption_manager.is_unlocked():
            raise RuntimeError("密码本未解锁")
        
        existing_ids = {entry.id for entry in self.db_session.query(PasswordEntryDB).all()}
        
        for entry_id, entry in entries.items():
            encrypted = self.encryption_manager.encrypt(entry.to_dict())
            encrypted_b64 = base64.b64encode(encrypted).decode('utf-8')
            
            if entry_id in existing_ids:
                entry_db = self.db_session.query(PasswordEntryDB).filter_by(id=entry_id).first()
                if entry_db:
                    entry_db.encrypted_data = encrypted_b64
                    entry_db.updated_at = datetime.now()
            else:
                entry_db = PasswordEntryDB(
                    id=entry_id,
                    encrypted_data=encrypted_b64,
                    created_at=entry.created_at,
                    updated_at=entry.updated_at
                )
                self.db_session.add(entry_db)
        
        for entry_id in existing_ids:
            if entry_id not in entries:
                entry_db = self.db_session.query(PasswordEntryDB).filter_by(id=entry_id).first()
                if entry_db:
                    self.db_session.delete(entry_db)
        
        self.db_session.commit()
        self._cache = entries.copy()
    
    def add_entry(self, entry: PasswordEntry) -> bool:
        """
        添加新的密码条目
        :param entry: PasswordEntry 实例
        :return: 是否添加成功
        """
        entries = self._load_from_db()
        
        if entry.id in entries:
            return False
        
        entries[entry.id] = entry
        self._save_to_db(entries)
        return True
    
    def get_entry(self, entry_id: str) -> Optional[PasswordEntry]:
        """
        根据 ID 获取密码条目
        :param entry_id: 条目 ID
        :return: PasswordEntry 实例或 None
        """
        entries = self._load_from_db()
        return entries.get(entry_id)
    
    def get_all_entries(self) -> List[PasswordEntry]:
        """
        获取所有密码条目
        :return: PasswordEntry 列表，按更新时间降序排列
        """
        entries = self._load_from_db()
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
        entries = self._load_from_db()
        
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
        
        self._save_to_db(entries)
        return True
    
    def delete_entry(self, entry_id: str) -> bool:
        """
        删除密码条目
        :param entry_id: 条目 ID
        :return: 是否删除成功
        """
        entries = self._load_from_db()
        
        if entry_id not in entries:
            return False
        
        del entries[entry_id]
        self._save_to_db(entries)
        return True
    
    def search_entries(self, query: str) -> List[PasswordEntry]:
        """
        搜索密码条目
        :param query: 搜索关键词
        :return: 匹配的 PasswordEntry 列表
        """
        entries = self._load_from_db()
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
        entries = self._load_from_db()
        
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
        entries = self._load_from_db()
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
        entries = self._load_from_db()
        return len(entries) == 0
    
    def get_total_count(self) -> int:
        """获取密码条目总数"""
        entries = self._load_from_db()
        return len(entries)
