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
            "is_custom": False,
            "icon_emoji": "🎯",
            "developer": "System",
        }


class GameRegistry:
    _games: Dict[str, BaseGamePlugin] = {}
    _custom_games: Dict[str, BaseGamePlugin] = {}

    @classmethod
    def register(cls, game: BaseGamePlugin) -> None:
        if game.slug in cls._games:
            raise ValueError(f"Game with slug '{game.slug}' is already registered")
        cls._games[game.slug] = game

    @classmethod
    def register_custom(cls, game: BaseGamePlugin) -> None:
        cls._custom_games[game.slug] = game

    @classmethod
    def unregister_custom(cls, slug: str) -> None:
        if slug in cls._custom_games:
            del cls._custom_games[slug]

    @classmethod
    def get(cls, slug: str) -> Optional[BaseGamePlugin]:
        if slug in cls._games:
            return cls._games.get(slug)
        return cls._custom_games.get(slug)

    @classmethod
    def get_all(cls) -> Dict[str, BaseGamePlugin]:
        all_games = cls._games.copy()
        all_games.update(cls._custom_games)
        return all_games

    @classmethod
    def list_games(cls) -> list:
        games = [game.get_info() for game in cls._games.values()]
        games.extend([game.get_info() for game in cls._custom_games.values()])
        return games

    @classmethod
    def clear_custom_games(cls) -> None:
        cls._custom_games.clear()
