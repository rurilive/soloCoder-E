import uuid
from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class PasswordCategory(str, Enum):
    """密码分类枚举"""
    SOCIAL = "社交账号"
    WORK = "工作账号"
    FINANCIAL = "金融账号"
    EMAIL = "邮箱账号"
    SHOPPING = "购物账号"
    GAMING = "游戏账号"
    OTHER = "其他"


class PasswordEntry(BaseModel):
    """密码条目数据模型"""
    
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str = Field(..., description="账号标题/名称")
    username: str = Field(default="", description="用户名/账号")
    password: str = Field(..., description="密码")
    url: str = Field(default="", description="关联的网址")
    category: PasswordCategory = Field(default=PasswordCategory.OTHER, description="分类")
    notes: str = Field(default="", description="备注信息")
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "id": "uuid-xxx",
                    "title": "GitHub 账号",
                    "username": "myusername",
                    "password": "********",
                    "url": "https://github.com",
                    "category": "工作账号",
                    "notes": "用于开发项目",
                    "created_at": "2024-01-01T00:00:00",
                    "updated_at": "2024-01-01T00:00:00"
                }
            ]
        }
    }
    
    def update_timestamp(self) -> None:
        """更新修改时间"""
        self.updated_at = datetime.now()
    
    def to_dict(self) -> dict:
        """转换为字典（用于序列化）"""
        category_value = self.category
        if isinstance(self.category, PasswordCategory):
            category_value = self.category.value
        elif hasattr(self.category, 'value'):
            category_value = self.category.value
        
        return {
            "id": self.id,
            "title": self.title,
            "username": self.username,
            "password": self.password,
            "url": self.url,
            "category": category_value,
            "notes": self.notes,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "PasswordEntry":
        """从字典创建实例"""
        category = data.get("category", "其他")
        
        if isinstance(category, PasswordCategory):
            pass
        elif isinstance(category, str):
            try:
                category = PasswordCategory(category)
            except ValueError:
                category = PasswordCategory.OTHER
        elif hasattr(category, 'value'):
            try:
                category = PasswordCategory(category.value)
            except (ValueError, TypeError):
                category = PasswordCategory.OTHER
        elif isinstance(category, dict):
            cat_value = category.get('value') or category.get('name') or "其他"
            if isinstance(cat_value, str):
                try:
                    category = PasswordCategory(cat_value)
                except ValueError:
                    category = PasswordCategory.OTHER
            else:
                category = PasswordCategory.OTHER
        else:
            category = PasswordCategory.OTHER
        
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        elif created_at is None:
            created_at = datetime.now()
        
        updated_at = data.get("updated_at")
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at)
        elif updated_at is None:
            updated_at = datetime.now()
        
        return cls(
            id=data.get("id"),
            title=data.get("title", ""),
            username=data.get("username", ""),
            password=data.get("password", ""),
            url=data.get("url", ""),
            category=category,
            notes=data.get("notes", ""),
            created_at=created_at,
            updated_at=updated_at
        )
