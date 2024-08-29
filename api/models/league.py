from collections import Counter
from datetime import datetime
from math import log1p

from beanie import Document
from pydantic import BaseModel, computed_field
from typing_extensions import Self

from api.consts import Champion
from api.models.match import MatchDocument, PlayerBase


class Stats(BaseModel):
    kills: int = 0
    deaths: int = 0
    assists: int = 0
    minions_killed: int = 0
    won: int = 0
    lost: int = 0


class Player(PlayerBase):
    stats: Stats
    picked_champions: list[Champion]

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

    @property
    @computed_field
    def most_picked_champion(self) -> Champion | None:
        if not self.picked_champions:
            return None  # or a default value such as Champion.UNKNOWN if applicable

        # Count the number of times each champion was picked
        counter = Counter(self.picked_champions)

        # Get the highest count (most common occurrence)
        most_common_champion, _ = counter.most_common(1)[0]
        return most_common_champion


class Standings(BaseModel):
    players: list[Player]
    start_date: datetime
    end_date: datetime
    matches: list[MatchDocument]

    @property
    @computed_field
    def matches_played(self):
        return len(self.matches)


class StandingsDocument(Standings, Document):
    class Settings:
        name = "standings"

    @classmethod
    async def get_standings_by_date(cls, start_date: datetime) -> Self | None:
        standings = await cls.find_one({"start_date": start_date})
        return standings

    async def refresh(self, match: MatchDocument):
        """
        Update the standings with data from a new or updated match.

        Args:
            match (MatchDocument): Match data to update standings with
        """
        players_in_match = match.players

        # Iterate through each player in the match
        for player_data in players_in_match:
            player_id = player_data.id
            player_stats = player_data.stats
            champion_played = player_data.champion

            # Find player in standings or add a new one if not found
            player = next((p for p in self.players if p.id == player_id), None)

            if not player:
                # If player does not exist in standings, create a new one
                player = Player(
                    id=player_id,
                    stats=Stats(),  # Initialize empty stats
                    most_picked_champion=champion_played,
                )
                self.players.append(player)

            # Update player stats
            player.stats.kills += player_stats.kills
            player.stats.deaths += player_stats.deaths
            player.stats.assists += player_stats.assists
            player.stats.minions_killed += player_stats.minions_killed

            if player.id in [player.id for _player in getattr(match, f"{match.winner}_team").players]:
                player.stats.won += 1
            else:
                player.stats.lost += 1

            player.picked_champions.append(champion_played)

        # Update the match list
        self.matches.append(match)

        # Save or update the standings document in the database
        await self.save()
