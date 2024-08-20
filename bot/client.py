from dataclasses import dataclass
from typing import Any

from beanie import init_beanie
from discord import Client, Intents, Message, utils

from api.db import get_db
from api.models.user import User
from bot.commands import ClientSingleton
from bot.commands.account import Register
from bot.commands.generic import Help
from bot.commands.match import Reset
from bot.db_utils import load_json
from bot.helpers import balance, beautify_teams


@dataclass
class Commands:
    register: Register = Register()
    reset: Reset = Reset()
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
        #     ("Princess RS", "EUW")
        # ]
        self.playing_list_ids = {}
        self.players = load_json().get("players")
        self.commands = Commands()

    async def on_ready(self):
        print(f"Logged on as {self.user}!")
        ClientSingleton.set_client(self)  # Set the client globally
        await init_beanie(database=get_db(), document_models=[User])

    async def send_ready_list(self, message):
        output_string = "Ready to play: \n"
        for index, player in enumerate(self.playing_list, start=1):
            output_string += (
                "{}. {}\n".format(index, player[0])
                if player[0] != len(self.playing_list) - 1
                else "{}. {}".format(index, player[0])
            )
        await message.channel.send(output_string)

    def refresh_players(self):
        self.players = load_json().get("players")

    async def on_message(self, message: Message):
        # we do not want the bot to reply to itself
        if message.author.id == self.user.id:
            return

        content = message.content
        author_id = str(message.author.id)
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
                # summoner = " ".join(summoner)
                # # find the # char
                # if "#" in summoner:
                #     summoner, tag = summoner.split("#")
                # else:
                #     tag = "euw"
                # register_player(summoner, author_id, tag)
                # self.refresh_players()
                # await message.channel.send(
                #     f"Username '{summoner}' and Tag '{tag}' successfully registered, tied to {message.author.name}"
                # )
            case ["!play"]:
                if len(self.playing_list) == 10:
                    await message.channel.send("The lobby is full.")
                else:
                    player = self.players.get(author_id)
                    if not player:
                        await message.channel.send("You are not registered, please register first.")
                        return
                    elif (player.get("summoner"), player.get("tag")) not in self.playing_list:
                        self.playing_list.append((player.get("summoner"), player.get("tag")))
                        self.playing_list_ids[player.get("summoner")] = author_id
                    await self.send_ready_list(message)
            case ["!remove"]:
                player = self.players.get(author_id)
                if (player.get("summoner"), player.get("tag")) in self.playing_list:
                    self.playing_list.remove((player.get("summoner"), player.get("tag")))
                    self.playing_list_ids.pop(player.get("summoner"))
                    await self.send_ready_list(message)
            case ["!close"]:
                if len(self.playing_list) < 10:
                    await message.channel.send("You don't have enough players to play, you need at least 10")
                else:
                    output_string = "Ready to play: \n"
                    for index, player in enumerate(self.playing_list, start=1):
                        output_string += "{}. {}\n".format(index, player[0])
                    await message.channel.send(output_string)
                    await message.channel.send("Starting the draw! Give me some seconds.")
                    blue_team, red_team, ranks = await balance(self.playing_list)
                    await message.channel.send(beautify_teams(blue_team, red_team, ranks, self.guilds[0].emojis))
                    blue_team_channel = utils.get(self.guilds[0].channels, name="Team 1")
                    red_team_channel = utils.get(self.guilds[0].channels, name="Team 2")
                    for player in blue_team.get("players"):
                        await (
                            self.guilds[0].get_member(int(self.playing_list_ids.get(player))).move_to(blue_team_channel)
                        )
                    for player in red_team.get("players"):
                        await (
                            self.guilds[0].get_member(int(self.playing_list_ids.get(player))).move_to(red_team_channel)
                        )


_intents = Intents.default()
_intents.message_content = True

client = MatchMaker(intents=_intents)
