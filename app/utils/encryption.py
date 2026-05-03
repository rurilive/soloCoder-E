import base64
import os
import hashlib
from pathlib import Path
from typing import Optional, Any
import json
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.backends import default_backend


class PasswordHasher:
    """主密码哈希管理器"""
    
    @staticmethod
    def hash_password(password: str, salt: Optional[bytes] = None) -> tuple[bytes, bytes]:
        """
        使用 PBKDF2 哈希密码
        返回 (hashed_password, salt)
        """
        if salt is None:
            salt = os.urandom(16)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        
        hashed = kdf.derive(password.encode('utf-8'))
        return hashed, salt
    
    @staticmethod
    def verify_password(password: str, stored_hash: bytes, stored_salt: bytes) -> bool:
        """验证密码是否匹配"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=stored_salt,
            iterations=100000,
            backend=default_backend()
        )
        
        try:
            kdf.verify(password.encode('utf-8'), stored_hash)
            return True
        except Exception:
            return False
    
    @staticmethod
    def password_to_fernet_key(password: str, salt: bytes) -> bytes:
        """
        将密码转换为 Fernet 密钥（32字节 -> base64编码）
        """
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        
        derived_key = kdf.derive(password.encode('utf-8'))
        return base64.urlsafe_b64encode(derived_key)


class EncryptionManager:
    """加密管理器，使用 Fernet 对称加密"""
    
    def __init__(self, key_file: Path, master_password: Optional[str] = None):
        """
        初始化加密管理器
        :param key_file: 密钥信息存储文件路径
        :param master_password: 用户主密码（可选，首次设置或验证时需要）
        """
        self.key_file = key_file
        self._fernet: Optional[Fernet] = None
        self._salt: Optional[bytes] = None
        self._password_hash: Optional[bytes] = None
        self._is_unlocked = False
    
    def is_master_password_set(self) -> bool:
        """检查是否已设置主密码"""
        return self.key_file.exists()
    
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
        
        data_to_store = {
            'salt': base64.b64encode(salt).decode('utf-8'),
            'password_hash': base64.b64encode(hashed_password).decode('utf-8')
        }
        
        with open(self.key_file, 'w', encoding='utf-8') as f:
            json.dump(data_to_store, f)
        
        self._salt = salt
        self._password_hash = hashed_password
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
            with open(self.key_file, 'r', encoding='utf-8') as f:
                stored_data = json.load(f)
            
            stored_salt = base64.b64decode(stored_data['salt'])
            stored_hash = base64.b64decode(stored_data['password_hash'])
            
            if not PasswordHasher.verify_password(password, stored_hash, stored_salt):
                return False
            
            fernet_key = PasswordHasher.password_to_fernet_key(password, stored_salt)
            
            self._salt = stored_salt
            self._password_hash = stored_hash
            self._fernet = Fernet(fernet_key)
            self._is_unlocked = True
            
            return True
            
        except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
            return False
    
    def lock(self) -> None:
        """锁定密码本，清除密钥"""
        self._fernet = None
        self._is_unlocked = False
    
    def is_unlocked(self) -> bool:
        """检查密码本是否已解锁"""
        return self._is_unlocked
    
    def encrypt(self, data: Any) -> bytes:
        """
        加密任意可序列化数据
        :param data: 要加密的数据（必须可序列化为 JSON）
        :return: 加密后的字节数据
        """
        if not self._is_unlocked or self._fernet is None:
            raise RuntimeError("密码本未解锁")
        
        json_str = json.dumps(data, ensure_ascii=False)
        encrypted = self._fernet.encrypt(json_str.encode('utf-8'))
        return encrypted
    
    def decrypt(self, encrypted_data: bytes) -> Any:
        """
        解密数据
        :param encrypted_data: 加密后的字节数据
        :return: 解密后的原始数据
        """
        if not self._is_unlocked or self._fernet is None:
            raise RuntimeError("密码本未解锁")
        
        try:
            decrypted_bytes = self._fernet.decrypt(encrypted_data)
            json_str = decrypted_bytes.decode('utf-8')
            return json.loads(json_str)
        except InvalidToken:
            raise ValueError("解密失败：数据可能已损坏或密钥不正确")
        except json.JSONDecodeError:
            raise ValueError("解密失败：数据格式错误")
    
    def encrypt_to_file(self, data: Any, file_path: Path) -> None:
        """加密数据并写入文件"""
        encrypted = self.encrypt(data)
        with open(file_path, 'wb') as f:
            f.write(encrypted)
    
    def decrypt_from_file(self, file_path: Path) -> Any:
        """从文件读取并解密数据"""
        if not file_path.exists():
            return None
        
        with open(file_path, 'rb') as f:
            encrypted_data = f.read()
        
        return self.decrypt(encrypted_data)
