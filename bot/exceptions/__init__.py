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
