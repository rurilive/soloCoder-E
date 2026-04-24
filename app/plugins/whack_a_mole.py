from typing import Any
from fastapi import Request
from fastapi.templating import Jinja2Templates
from app.plugins.base import BaseGamePlugin


class WhackAMolePlugin(BaseGamePlugin):
    @property
    def name(self) -> str:
        return "Whack-a-Mole"

    @property
    def slug(self) -> str:
        return "whack-a-mole"

    @property
    def description(self) -> str:
        return "A classic whack-a-mole game. Hit the moles as they appear!"

    @property
    def template_name(self) -> str:
        return "games/whack_a_mole.html"

    async def play(self, request: Request, templates: Jinja2Templates) -> Any:
        return templates.TemplateResponse(
            request,
            self.template_name,
            {
                "game_name": self.name,
                "game_slug": self.slug,
            },
        )
