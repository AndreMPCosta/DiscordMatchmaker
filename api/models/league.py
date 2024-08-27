from datetime import datetime
from math import log1p

from beanie import Document
from pydantic import BaseModel, computed_field

from api.consts import Champion
from api.models.match import MatchDocument, PlayerBase


class Stats(BaseModel):
    kills: int
    deaths: int
    assists: int
    minions_killed: int
    won: int
    lost: int


class Player(PlayerBase):
    stats: Stats
    most_picked_champion: Champion

    @property
    @computed_field
    def kda(self) -> float:
        return (
            (self.stats.kills + self.stats.assists) / self.stats.deaths
            if self.stats.deaths
            else self.stats.kills + self.stats.assists
        )

    @property
    @computed_field
    def win_rate(self) -> float:
        return self.stats.won / (self.stats.won + self.stats.lost) * 100

    @property
    @computed_field
    def matches_played(self) -> int:
        return self.stats.won + self.stats.lost

    @property
    @computed_field
    def points(self) -> int:
        total_matches = self.matches_played
        base_points = self.stats.won * 3  # 3 points per win

        # Penalty factor calculation using win rate and logarithmic scaling
        if total_matches > 0:
            penalty_factor = self.win_rate / (1 + log1p(total_matches))
        else:
            penalty_factor = 0

        # Points calculation formula
        points = base_points * penalty_factor

        return int(points)


class Standings(BaseModel):
    players: Player
    start_date: datetime
    end_date: datetime
    matches: list[MatchDocument]

    @property
    @computed_field
    def matches_played(self):
        return len(self.matches)


class StandingsDocument(Document):
    class Settings:
        name = "standings"
