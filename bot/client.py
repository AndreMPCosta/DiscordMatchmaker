from dataclasses import dataclass
from typing import Any

from beanie import init_beanie
from discord import Client, Intents, Message

from api.db import get_db
from api.models.user import User
from bot.commands import ClientSingleton
from bot.commands.account import Register
from bot.commands.generic import Help
from bot.commands.match import Close, Play, Remove, Reset, Upload
from bot.db_utils import load_json


@dataclass
class Commands:
    register: Register = Register()
    reset: Reset = Reset()
    play: Play = Play()
    remove: Remove = Remove()
    close: Close = Close()
    upload: Upload = Upload()
    help: Help = Help()


class MatchMaker(Client):
    def __init__(self, *, intents: Intents, **options: Any):
        super().__init__(intents=intents, **options)
        self.playing_list = []
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
        self.players = load_json().get("players")
        self.commands = Commands()

    async def on_ready(self):
        print(f"Logged on as {self.user}!")
        ClientSingleton.set_client(self)  # Set the client globally
        await init_beanie(database=get_db(), document_models=[User])

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
            case ["!reset"]:
                self.playing_list = []
                self.playing_list_ids = {}
            case ["!playlist"]:
                await self.send_ready_list(message)
            case ["!register", *summoner]:
                await getattr(self.commands, "register").execute(message, summoner)
            case _:  # default
                await getattr(self.commands, content.split()[0].replace("!", "")).execute(message)


_intents = Intents.default()
_intents.message_content = True

client = MatchMaker(intents=_intents)
