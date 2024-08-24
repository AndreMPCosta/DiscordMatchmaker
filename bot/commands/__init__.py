from abc import ABC, abstractmethod
from dataclasses import dataclass
from json import dumps
from typing import TYPE_CHECKING

from discord import Message

if TYPE_CHECKING:
    from bot.client import MatchMaker


class ClientSingleton:
    _instance = None

    @classmethod
    def set_client(cls, client):
        cls._instance = client

    @classmethod
    def get_client(cls):
        if cls._instance is None:
            raise RuntimeError("Client is not set")
        return cls._instance


@dataclass
class Command(ABC):
    name: str
    description: str
    usage: str
    example: str

    @property
    def client(self) -> "MatchMaker":
        return ClientSingleton.get_client()

    @abstractmethod
    async def execute(self, message: Message, *args):
        pass

    async def show_help(self, message: Message):
        description = self.description
        usage = self.usage
        example = f"\n{self.example}" if self.example != self.usage else None
        _message = f"{description}\n" f"Usage: {usage}{f'Example: {example}' if example else ''}"
        await message.channel.send(_message)

    async def update_redis_playing_list(self):
        await self.client.redis.set("playing_list", dumps(self.client.playing_list))
        await self.client.redis.set("playing_list_ids", dumps(self.client.playing_list_ids))

    async def update_redis_last_match(self):
        await self.client.redis.set("last_match_id", str(self.client.last_match.id))
