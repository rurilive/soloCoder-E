#!/usr/bin/env python3
"""测试修复后的代码"""

import sys
sys.path.insert(0, '.')

from app.models.password_entry import PasswordEntry, PasswordCategory
from datetime import datetime


def test_from_dict_with_various_category_types():
    """测试 from_dict 处理各种类型的 category"""
    
    print("测试 1: category 是字符串")
    data1 = {
        "id": "test1",
        "title": "测试账号1",
        "username": "user1",
        "password": "pass1",
        "url": "https://example.com",
        "category": "工作账号",
        "notes": "测试1",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    entry1 = PasswordEntry.from_dict(data1)
    print(f"  category 类型: {type(entry1.category)}")
    print(f"  category 值: {entry1.category}")
    print(f"  category.value: {entry1.category.value}")
    assert entry1.category == PasswordCategory.WORK
    print("  ✓ 通过\n")
    
    print("测试 2: category 是字典 (模拟损坏的数据)")
    data2 = {
        "id": "test2",
        "title": "测试账号2",
        "username": "user2",
        "password": "pass2",
        "url": "https://example.com",
        "category": {"value": "社交账号", "name": "SOCIAL"},
        "notes": "测试2",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    entry2 = PasswordEntry.from_dict(data2)
    print(f"  category 类型: {type(entry2.category)}")
    print(f"  category 值: {entry2.category}")
    print(f"  category.value: {entry2.category.value}")
    assert entry2.category == PasswordCategory.SOCIAL
    print("  ✓ 通过\n")
    
    print("测试 3: category 是无效字典，应默认到 OTHER")
    data3 = {
        "id": "test3",
        "title": "测试账号3",
        "username": "user3",
        "password": "pass3",
        "url": "https://example.com",
        "category": {"invalid_key": "无效值"},
        "notes": "测试3",
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    }
    entry3 = PasswordEntry.from_dict(data3)
    print(f"  category 类型: {type(entry3.category)}")
    print(f"  category 值: {entry3.category}")
    assert entry3.category == PasswordCategory.OTHER
    print("  ✓ 通过\n")
    
    print("测试 4: to_dict 序列化")
    entry_dict = entry1.to_dict()
    print(f"  to_dict 结果: {entry_dict}")
    print(f"  category 类型: {type(entry_dict['category'])}")
    print(f"  category 值: {entry_dict['category']}")
    assert entry_dict['category'] == "工作账号"
    print("  ✓ 通过\n")
    
    print("测试 5: 循环 - to_dict -> from_dict")
    entry_dict = entry1.to_dict()
    entry_reloaded = PasswordEntry.from_dict(entry_dict)
    print(f"  原始 category: {entry1.category}")
    print(f"  重新加载 category: {entry_reloaded.category}")
    assert entry_reloaded.category == entry1.category
    print("  ✓ 通过\n")


if __name__ == "__main__":
    print("=" * 50)
    print("开始测试修复后的代码...")
    print("=" * 50 + "\n")
    
    try:
        test_from_dict_with_various_category_types()
        print("✓ 所有测试通过!")
    except Exception as e:
        print(f"✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
