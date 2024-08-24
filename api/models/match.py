from datetime import datetime
from typing import Annotated, Literal

from beanie import Document
from dateparser import parse
from pydantic import BaseModel, BeforeValidator, Field


def convert_to_date(date: str) -> datetime:
    return parse(date)


class PlayerStats(BaseModel):
    kills: int
    deaths: int
    assists: int
    minions_killed: int
    gold_earned: int
    level: int

    @property
    def kda(self) -> float:
        return (self.kills + self.assists) / self.deaths if self.deaths else self.kills + self.assists


class TeamStats(BaseModel):
    kills: int
    deaths: int
    assists: int
    total_gold: int
    towers_destroyed: int
    inhibitors_destroyed: int
    barons_slain: int
    dragons_slain: int
    rift_heralds_slain: int
    void_grubs_slain: int


class Player(BaseModel):
    name: str
    picked_champion: str | None = None
    stats: PlayerStats


class Team(BaseModel):
    players: list[Player]
    bans: list[str] = Field(default_factory=list)
    stats: TeamStats


class Match(BaseModel):
    blue_team: Team
    red_team: Team
    duration: str
    date: Annotated[datetime, BeforeValidator(convert_to_date)]
    winner: Literal["blue", "red"]
    mvp: str | None = None


class MatchDocument(Document, Match):
    class Settings:
        collection = "matches"
        indexes = ["date", "winner"]
