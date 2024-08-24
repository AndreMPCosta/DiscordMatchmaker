from datetime import datetime
from typing import Annotated, Literal

from beanie import Document
from dateparser import parse
from discord import Embed
from prettytable import PrettyTable
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

    def create_embed(self) -> Embed:
        """
        Create an embed object with the match details.

        Returns:
            A discord.Embed object.
        """

        # Extract game details
        date = self.date.strftime("%d/%m/%Y")  # Format date for better readability
        duration = self.duration
        winner = self.winner.capitalize()  # Capitalize winner name

        # Create embed object
        embed = Embed(title=f"League of Legends Game Summary - {winner} Wins", color=0x00FFFF)
        embed.add_field(name="Date", value=date, inline=True)
        embed.add_field(name="Duration", value=duration, inline=True)

        # Team Stats
        table = PrettyTable()
        table.field_names = [
            "Team",
            "Kills",
            "Deaths",
            "Assists",
            "Total Gold",
            "Towers",
            "Inhibitors",
            "Barons",
            "Dragons",
            "Rift Heralds",
            "Void Grubs",
        ]

        for index, team in enumerate((self.blue_team, self.red_team)):
            table.add_row(
                [
                    "BLUE" if index == 0 else "RED",
                    team.stats.kills,
                    team.stats.deaths,
                    team.stats.assists,
                    team.stats.total_gold,
                    team.stats.towers_destroyed,
                    team.stats.inhibitors_destroyed,
                    team.stats.barons_slain,
                    team.stats.dragons_slain,
                    team.stats.rift_heralds_slain,
                    team.stats.void_grubs_slain,
                ]
            )
        embed.add_field(name="Team Stats", value=table.get_string(sortby="Team"), inline=False)

        # Player data
        table = PrettyTable()
        table.field_names = ["Player", "Champion", "Kills", "Deaths", "Assists", "KDA", "Minions", "Gold", "Level"]
        for index, team in enumerate((self.blue_team, self.red_team)):
            for player in team.players:
                table.add_row(
                    [
                        player.name,
                        player.picked_champion,
                        player.stats.kills,
                        player.stats.deaths,
                        player.stats.assists,
                        f"{player.stats.kda:.2f}",
                        player.stats.minions_killed,
                        player.stats.gold_earned,
                        player.stats.level,
                    ]
                )
            embed.add_field(
                name=f"Player Stats {'BLUE' if index == 0 else 'RED'}", value=table.get_string(), inline=False
            )

        return embed


class MatchDocument(Document, Match):
    class Settings:
        collection = "matches"
        indexes = ["date", "winner"]
