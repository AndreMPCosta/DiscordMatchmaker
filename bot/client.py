from dataclasses import dataclass
from json import loads
from typing import Any

from aioredis import Redis
from beanie import PydanticObjectId, init_beanie
from discord import Client, Intents, Message

from api.db import get_db
from api.models.match import MatchDocument, Player
from api.models.user import User
from bot.commands import ClientSingleton
from bot.commands.account import Register
from bot.commands.generic import Help
from bot.commands.match import Close, Play, Playlist, Remove, Reset, Upload
from bot.commands.post_match import ForceVote, MVPList, ShowMissing, Vote
from clients.redis import retrieve_async_redis_client


@dataclass
class Commands:
    register: Register = Register()
    reset: Reset = Reset()
    play: Play = Play()
    playlist: Playlist = Playlist()
    remove: Remove = Remove()
    close: Close = Close()
    upload: Upload = Upload()
    vote: Vote = Vote()
    force_vote: ForceVote = ForceVote()
    show_missing: ShowMissing = ShowMissing()
    mvp: MVPList = MVPList()
    help: Help = Help()


class MatchMaker(Client):
    def __init__(self, *, intents: Intents, **options: Any):
        super().__init__(intents=intents, **options)
        self.redis: Redis = retrieve_async_redis_client()
        self.playing_list: list[tuple[str, str]] = []
        self.last_match: MatchDocument | None = None
        self.last_match_id: PydanticObjectId | None = None
        self.mvp_votes: dict[int, Player] = dict()
        self.eligible_mvps: list[Player] = []
        # [
        #     ("Demon Hand", "Water"),
        #     ("NinaKravitzzz", "EUW"),
        #     ("Mazzeee", "EUW"),
        #     ("sinj", "sinji"),
        #     ("flemsss", "EUW"),
        #     ("salganhadaa", "simor"),
        #     ("Filipados", "EUW"),
        #     ("Godzela", "EUW"),
        #     ("CrazedAfro", "EUW"),
        #     ("2n2u", "EUW"),
        # ]
        self.playing_list_ids = {}
        self.commands = Commands()

    async def on_ready(self):
        print(f"Logged on as {self.user}!")
        ClientSingleton.set_client(self)  # Set the client globally
        await init_beanie(database=get_db(), document_models=[User])
        from_redis_playing_list = await self.redis.get("playing_list")
        from_redis_playing_list_ids = await self.redis.get("playing_list_ids")
        redis_match_id = await self.redis.get("last_match_id")
        from_redis_last_match_id = redis_match_id if redis_match_id else None
        self.playing_list = (
            [(player, tag) for player, tag in loads(from_redis_playing_list)] if from_redis_playing_list else []
        )
        # self.playing_list = [
        #     ("PretinhoDaGuiné", "EUW"),
        #     ("Elesh95", "EUW"),
        #     ("Toy", "2228"),
        #     ("popping off", "EUW"),
        #     ("Mazzeee", "EUW"),
        #     ("locked in", "EUW"),
        #     ("zau", "EUW"),
        #     ("salganhadaa", "SIMOR"),
        #     ("Filipados", "EUW"),
        #     ("Cardoso00", "EUW"),
        # ]
        self.playing_list_ids = loads(from_redis_playing_list_ids) if from_redis_playing_list_ids else {}
        self.last_match_id = PydanticObjectId(from_redis_last_match_id) if from_redis_last_match_id else None

    async def send_ready_list(self, message: Message):
        output_string = "Ready to play: \n"
        for index, player in enumerate(self.playing_list, start=1):
            output_string += (
                "{}. {}\n".format(index, player[0])
                if player[0] != len(self.playing_list) - 1
                else "{}. {}".format(index, player[0])
            )
        await message.channel.send(output_string)

    async def on_message(self, message: Message):
        # we do not want the bot to reply to itself
        if message.author.id == self.user.id:
            return

        content = message.content
        match content.split():
            case ["!help", *command]:
                command = " ".join(command)
                if command:
                    await getattr(self.commands, command).show_help(message)
                else:
                    await self.commands.help.execute(message)
            case ["!ping"]:
                await message.channel.send("pong")
            case ["!register", *summoner]:
                await getattr(self.commands, "register").execute(message, summoner)
                await self.commands.register.show_log(message, summoner)
            case ["!vote", *player]:
                await getattr(self.commands, "vote").execute(message, player, message.author.id)
                await self.commands.vote.show_log(message, player)
            case ["!force_vote", *player]:
                await getattr(self.commands, "force_vote").execute(message, player)
                await self.commands.force_vote.show_log(message, player)
            case _:  # default
                if "!" in content[0]:
                    await getattr(self.commands, content.split()[0].replace("!", "")).execute(message)
                    await getattr(self.commands, content.split()[0].replace("!", "")).show_log(message)


_intents = Intents.default()
_intents.message_content = True

client = MatchMaker(intents=_intents)
