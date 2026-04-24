from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from fastapi import Request
from fastapi.templating import Jinja2Templates


class BaseGamePlugin(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def slug(self) -> str:
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        pass

    @property
    @abstractmethod
    def template_name(self) -> str:
        pass

    @abstractmethod
    async def play(self, request: Request, templates: Jinja2Templates) -> Any:
        pass

    def get_info(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "slug": self.slug,
            "description": self.description,
        }


class GameRegistry:
    _games: Dict[str, BaseGamePlugin] = {}

    @classmethod
    def register(cls, game: BaseGamePlugin) -> None:
        if game.slug in cls._games:
            raise ValueError(f"Game with slug '{game.slug}' is already registered")
        cls._games[game.slug] = game

    @classmethod
    def get(cls, slug: str) -> Optional[BaseGamePlugin]:
        return cls._games.get(slug)

    @classmethod
    def get_all(cls) -> Dict[str, BaseGamePlugin]:
        return cls._games.copy()

    @classmethod
    def list_games(cls) -> list:
        return [game.get_info() for game in cls._games.values()]
