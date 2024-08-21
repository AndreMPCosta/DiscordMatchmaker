from beanie import Document
from pydantic import BaseModel


class Stats(BaseModel):
    kills: int
    deaths: int
    assists: int
    minions_killed: int
    gold_earned: float
    level: int

    @property
    def kda(self) -> float:
        return (self.kills + self.assists) / self.deaths if self.deaths else self.kills + self.assists


class Player(BaseModel):
    name: str
    stats: Stats


class Match(Document):
    team_1: list[Player]
    team_2: list[Player]
