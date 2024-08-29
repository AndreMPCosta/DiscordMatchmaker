from dataclasses import dataclass


@dataclass
class BotException(Exception):
    detail: str


class SummonerNotFound(BotException):
    def __init__(self, summoner: str, tag: str):
        self.detail = (
            f"Summoner '{summoner}' with tag '{tag}' not found. "
            f"Please make sure the summoner name and tag are correct."
        )


class ChampionMismatch(BotException):
    def __init__(self, champion: str | None):
        self.detail = f"Champion '{champion}' not found. Please make sure the champion name is correct."


class GeminiError(BotException):
    def __init__(self):
        self.detail = "An error occurred while processing the image"
