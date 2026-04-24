from typing import Any, Dict
from fastapi import Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pathlib import Path
from app.plugins.base import BaseGamePlugin
from app.config import settings


class CustomGamePlugin(BaseGamePlugin):
    def __init__(
        self,
        name: str,
        slug: str,
        description: str,
        game_path: str,
        developer: str = "User",
        icon_emoji: str = "🎮",
        instructions: str = None,
    ):
        self._name = name
        self._slug = slug
        self._description = description
        self._game_path = game_path
        self._developer = developer
        self._icon_emoji = icon_emoji
        self._instructions = instructions

    @property
    def name(self) -> str:
        return self._name

    @property
    def slug(self) -> str:
        return self._slug

    @property
    def description(self) -> str:
        return self._description

    @property
    def template_name(self) -> str:
        return "games/custom_game.html"

    @property
    def game_path(self) -> str:
        return self._game_path

    @property
    def developer(self) -> str:
        return self._developer

    @property
    def icon_emoji(self) -> str:
        return self._icon_emoji

    @property
    def instructions(self) -> str:
        return self._instructions

    def get_info(self) -> Dict[str, Any]:
        info = super().get_info()
        info.update({
            "developer": self._developer,
            "icon_emoji": self._icon_emoji,
            "instructions": self._instructions,
            "is_custom": True,
        })
        return info

    async def play(self, request: Request, templates: Jinja2Templates) -> Any:
        game_full_path = settings.CUSTOM_GAMES_DIR / self._game_path
        index_html = game_full_path / "index.html"
        
        if not index_html.exists():
            return HTMLResponse(
                content=f"<h1>Game Not Found</h1><p>The game '{self._name}' could not be loaded.</p>",
                status_code=404
            )
        
        game_iframe_url = f"/games/iframe/{self._slug}"
        
        return templates.TemplateResponse(
            request,
            self.template_name,
            {
                "game_name": self._name,
                "game_slug": self._slug,
                "game_iframe_url": game_iframe_url,
                "game_icon": self._icon_emoji,
                "instructions": self._instructions,
                "developer": self._developer,
            },
        )
