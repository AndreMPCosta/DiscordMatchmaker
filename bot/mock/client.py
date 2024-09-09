from asyncio import run

from beanie import init_beanie
from discord import Intents

from api.db import get_db
from api.models.league import StandingsDocument
from api.models.match import MatchDocument
from api.models.user import User
from bot.client import MatchMaker

_intents = Intents.default()
_intents.message_content = True


class MockClient(MatchMaker):
    def __init__(self):
        super().__init__(intents=_intents)
        self.playing_list_ids = {}
        self.last_match_id = None
        self.playing_list = [
            ("PretinhoDaGuiné", "EUW"),
            ("Filipados", "EUW"),
            ("Mazzeee", "EUW"),
            ("Sinj", "sinji"),
            ("flemsss", "EUW"),
            ("sirGOD", "EUW"),
            ("madafz", "EUW"),
            ("spark in dark", "EUW"),
            ("CrazedAfro", "EUW"),
            ("Homem do Saco", "EUW"),
        ]
        run(self.initialize())  # Use asyncio.run() once

    async def initialize(self):
        await self.delayed_init()
        await self.populate_playing_list_ids()

    @staticmethod
    async def delayed_init():
        await init_beanie(
            database=get_db(),
            document_models=[
                User,
                MatchDocument,
                StandingsDocument,
            ],
        )

    async def populate_playing_list_ids(self):
        for player in self.playing_list:
            user = await User.find_one({"summoner": {"$regex": rf"^{player[0]}$", "$options": "i"}})
            self.playing_list_ids[player[0]] = user.discord_id
