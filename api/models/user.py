from datetime import datetime

from beanie import Document
from pydantic import Field
from pymongo import IndexModel
from typing_extensions import Self


class User(Document):
    discord_id: int = Field(..., description="The Discord user ID")
    summoner: str = Field(..., description="The summoner name")
    tag: str = Field(default="EUW", description="The region tag")
    creation_date: datetime = Field(default_factory=datetime.utcnow)
    last_modified: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "users"
        description = "User"
        indexes = [
            IndexModel("discord_id", name="discord_id_index", background=True, unique=True),
        ]
        use_revision = True

    @classmethod
    async def get_by_discord_id(cls, discord_id: int) -> Self | None:
        return await cls.find_one({"discord_id": discord_id})
