from datetime import timedelta
from fastapi import APIRouter, Request, Depends, Form, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from sqlalchemy.orm import Session
from app.database import get_db
from app.auth import (
    get_current_user,
    get_current_user_or_401,
    authenticate_user,
    create_user,
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
)
from app.config import settings

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    user = await get_current_user(request)
    if user:
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse(
        request,
        "auth/login.html",
        {"user": None, "error": None},
    )


@router.post("/login")
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = authenticate_user(db, username, password)
    if not user:
        return templates.TemplateResponse(
            request,
            "auth/login.html",
            {"user": None, "error": "用户名或密码错误"},
        )
    
    access_token = create_access_token(
        data={
            "user_id": user.id,
            "username": user.username,
            "display_name": user.display_name,
        },
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    
    response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    response.set_cookie(
        key=settings.COOKIE_NAME,
        value=access_token,
        httponly=True,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    return response


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    user = await get_current_user(request)
    if user:
        return RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse(
        request,
        "auth/register.html",
        {"user": None, "error": None},
    )


@router.post("/register")
async def register(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...),
    email: str = Form(None),
    display_name: str = Form(None),
    db: Session = Depends(get_db),
):
    from app.auth import get_user_by_username
    
    if password != confirm_password:
        return templates.TemplateResponse(
            request,
            "auth/register.html",
            {"user": None, "error": "两次密码输入不一致"},
        )
    
    if get_user_by_username(db, username):
        return templates.TemplateResponse(
            request,
            "auth/register.html",
            {"user": None, "error": "用户名已存在"},
        )
    
    user = create_user(
        db,
        username=username,
        password=password,
        email=email,
        display_name=display_name,
    )
    
    access_token = create_access_token(
        data={
            "user_id": user.id,
            "username": user.username,
            "display_name": user.display_name,
        },
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    
    response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    response.set_cookie(
        key=settings.COOKIE_NAME,
        value=access_token,
        httponly=True,
        max_age=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    return response


@router.get("/logout")
async def logout(request: Request):
    response = RedirectResponse(url="/auth/login", status_code=status.HTTP_302_FOUND)
    response.delete_cookie(key=settings.COOKIE_NAME)
    return response
