from fastapi import APIRouter, Request, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from typing import Optional
from starlette import status
from pathlib import Path

from app.config import settings
from app.utils.encryption import EncryptionManager
from app.models.storage import StorageManager
from app.models.password_entry import PasswordEntry, PasswordCategory


router = APIRouter()

templates = Jinja2Templates(directory=str(settings.TEMPLATES_DIR))

_encryption_manager: Optional[EncryptionManager] = None
_storage_manager: Optional[StorageManager] = None
_session_unlocked = False


def get_encryption_manager() -> EncryptionManager:
    """获取加密管理器单例"""
    global _encryption_manager
    if _encryption_manager is None:
        _encryption_manager = EncryptionManager(settings.ENCRYPTION_KEY_FILE)
    return _encryption_manager


def get_storage_manager() -> StorageManager:
    """获取存储管理器单例"""
    global _storage_manager
    if _storage_manager is None:
        enc_manager = get_encryption_manager()
        _storage_manager = StorageManager(enc_manager, settings.PASSWORD_STORAGE_FILE)
    return _storage_manager


def is_unlocked() -> bool:
    """检查是否已解锁"""
    global _session_unlocked
    enc_manager = get_encryption_manager()
    return enc_manager.is_unlocked()


def require_unlocked(request: Request):
    """依赖项：要求已解锁"""
    enc_manager = get_encryption_manager()
    if not enc_manager.is_unlocked():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="密码本未解锁"
        )
    return True


@router.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """主页：根据状态重定向"""
    enc_manager = get_encryption_manager()
    
    if not enc_manager.is_master_password_set():
        return RedirectResponse(url="/setup", status_code=status.HTTP_302_FOUND)
    
    if not enc_manager.is_unlocked():
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    
    return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)


@router.get("/setup", response_class=HTMLResponse)
async def setup_page(request: Request):
    """设置主密码页面"""
    enc_manager = get_encryption_manager()
    
    if enc_manager.is_master_password_set():
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    
    return templates.TemplateResponse(
        "setup.html",
        {"request": request, "settings": settings}
    )


@router.post("/setup", response_class=HTMLResponse)
async def setup_master_password(
    request: Request,
    password: str = Form(...),
    confirm_password: str = Form(...)
):
    """处理设置主密码"""
    enc_manager = get_encryption_manager()
    
    if enc_manager.is_master_password_set():
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    
    if password != confirm_password:
        return templates.TemplateResponse(
            "setup.html",
            {
                "request": request,
                "settings": settings,
                "error": "两次输入的密码不一致"
            }
        )
    
    if len(password) < 6:
        return templates.TemplateResponse(
            "setup.html",
            {
                "request": request,
                "settings": settings,
                "error": "密码长度至少为6位"
            }
        )
    
    enc_manager.setup_master_password(password)
    
    return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """登录/解锁页面"""
    enc_manager = get_encryption_manager()
    
    if not enc_manager.is_master_password_set():
        return RedirectResponse(url="/setup", status_code=status.HTTP_302_FOUND)
    
    if enc_manager.is_unlocked():
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    
    return templates.TemplateResponse(
        "login.html",
        {"request": request, "settings": settings}
    )


@router.post("/login", response_class=HTMLResponse)
async def login(request: Request, password: str = Form(...)):
    """处理登录/解锁"""
    enc_manager = get_encryption_manager()
    
    if not enc_manager.is_master_password_set():
        return RedirectResponse(url="/setup", status_code=status.HTTP_302_FOUND)
    
    if enc_manager.unlock(password):
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    else:
        return templates.TemplateResponse(
            "login.html",
            {
                "request": request,
                "settings": settings,
                "error": "密码错误"
            }
        )


@router.get("/lock")
async def lock():
    """锁定密码本"""
    enc_manager = get_encryption_manager()
    enc_manager.lock()
    return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, category: Optional[str] = None, search: Optional[str] = None):
    """仪表盘页面"""
    enc_manager = get_encryption_manager()
    storage_manager = get_storage_manager()
    
    if not enc_manager.is_master_password_set():
        return RedirectResponse(url="/setup", status_code=status.HTTP_302_FOUND)
    
    if not enc_manager.is_unlocked():
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    
    if search:
        entries = storage_manager.search_entries(search)
    elif category:
        try:
            cat = PasswordCategory(category)
            entries = storage_manager.get_entries_by_category(cat)
        except ValueError:
            entries = storage_manager.get_all_entries()
    else:
        entries = storage_manager.get_all_entries()
    
    categories_count = storage_manager.get_categories_count()
    total_count = storage_manager.get_total_count()
    
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "settings": settings,
            "entries": entries,
            "categories_count": categories_count,
            "total_count": total_count,
            "current_category": category,
            "search_query": search,
            "PasswordCategory": PasswordCategory
        }
    )


@router.get("/add", response_class=HTMLResponse)
async def add_entry_page(request: Request):
    """添加密码条目页面"""
    enc_manager = get_encryption_manager()
    
    if not enc_manager.is_unlocked():
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    
    return templates.TemplateResponse(
        "entry_form.html",
        {
            "request": request,
            "settings": settings,
            "entry": None,
            "PasswordCategory": PasswordCategory,
            "is_edit": False
        }
    )


@router.post("/add", response_class=HTMLResponse)
async def add_entry(
    request: Request,
    title: str = Form(...),
    username: str = Form(default=""),
    password: str = Form(...),
    url: str = Form(default=""),
    category: str = Form(default="其他"),
    notes: str = Form(default="")
):
    """处理添加密码条目"""
    enc_manager = get_encryption_manager()
    storage_manager = get_storage_manager()
    
    if not enc_manager.is_unlocked():
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    
    try:
        cat = PasswordCategory(category)
    except ValueError:
        cat = PasswordCategory.OTHER
    
    entry = PasswordEntry(
        title=title,
        username=username,
        password=password,
        url=url,
        category=cat,
        notes=notes
    )
    
    storage_manager.add_entry(entry)
    
    return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)


@router.get("/edit/{entry_id}", response_class=HTMLResponse)
async def edit_entry_page(request: Request, entry_id: str):
    """编辑密码条目页面"""
    enc_manager = get_encryption_manager()
    storage_manager = get_storage_manager()
    
    if not enc_manager.is_unlocked():
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    
    entry = storage_manager.get_entry(entry_id)
    if entry is None:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    
    return templates.TemplateResponse(
        "entry_form.html",
        {
            "request": request,
            "settings": settings,
            "entry": entry,
            "PasswordCategory": PasswordCategory,
            "is_edit": True
        }
    )


@router.post("/edit/{entry_id}", response_class=HTMLResponse)
async def edit_entry(
    request: Request,
    entry_id: str,
    title: str = Form(...),
    username: str = Form(default=""),
    password: str = Form(...),
    url: str = Form(default=""),
    category: str = Form(default="其他"),
    notes: str = Form(default="")
):
    """处理编辑密码条目"""
    enc_manager = get_encryption_manager()
    storage_manager = get_storage_manager()
    
    if not enc_manager.is_unlocked():
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    
    updated_data = {
        "title": title,
        "username": username,
        "password": password,
        "url": url,
        "category": category,
        "notes": notes
    }
    
    storage_manager.update_entry(entry_id, updated_data)
    
    return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)


@router.get("/view/{entry_id}", response_class=HTMLResponse)
async def view_entry(request: Request, entry_id: str):
    """查看密码条目详情"""
    enc_manager = get_encryption_manager()
    storage_manager = get_storage_manager()
    
    if not enc_manager.is_unlocked():
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    
    entry = storage_manager.get_entry(entry_id)
    if entry is None:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    
    return templates.TemplateResponse(
        "view_entry.html",
        {
            "request": request,
            "settings": settings,
            "entry": entry
        }
    )


@router.get("/delete/{entry_id}", response_class=HTMLResponse)
async def delete_entry_confirm(request: Request, entry_id: str):
    """删除确认页面"""
    enc_manager = get_encryption_manager()
    storage_manager = get_storage_manager()
    
    if not enc_manager.is_unlocked():
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    
    entry = storage_manager.get_entry(entry_id)
    if entry is None:
        return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
    
    return templates.TemplateResponse(
        "delete_confirm.html",
        {
            "request": request,
            "settings": settings,
            "entry": entry
        }
    )


@router.post("/delete/{entry_id}", response_class=HTMLResponse)
async def delete_entry(request: Request, entry_id: str):
    """处理删除密码条目"""
    enc_manager = get_encryption_manager()
    storage_manager = get_storage_manager()
    
    if not enc_manager.is_unlocked():
        return RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    
    storage_manager.delete_entry(entry_id)
    
    return RedirectResponse(url="/dashboard", status_code=status.HTTP_302_FOUND)
