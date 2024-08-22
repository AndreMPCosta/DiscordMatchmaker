from datetime import datetime
from typing import Literal

from beanie import Document
from pydantic import BaseModel, Field


class PlayerStats(BaseModel):
    kills: int
    deaths: int
    assists: int
    minions_killed: int
    gold_earned: float
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


class Match(Document):
    blue_team: Team
    red_team: Team
    duration: str
    date: datetime
    winner: Literal["blue", "red"]
