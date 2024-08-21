from dataclasses import dataclass, field

from aiohttp import ClientSession
import cv2
from discord import utils
import numpy as np

from api.models.user import User
from bot.commands import Command
from bot.helpers import balance, beautify_teams
from bot.ingestion.match import ImageRecognition


@dataclass
class Reset(Command):
    name: str = "reset"
    description: str = "Reset the lobby playing list"
    usage: str = "!reset"
    example: str = "!reset"

    async def execute(self, message, *args):
        self.client.playing_list = []
        self.client.playing_list_ids = {}
        await message.channel.send("Lobby has been reset.")


@dataclass
class Play(Command):
    name: str = "play"
    description: str = "Join the lobby"
    usage: str = "!play"
    example: str = "!play"

    async def execute(self, message, *args):
        if len(self.client.playing_list) == 10:
            await message.channel.send("The lobby is full.")
        else:
            player = await User.get_by_discord_id(int(message.author.id))
            if not player:
                await message.channel.send("You are not registered, please register first.")
                return
            elif (player.summoner, player.tag) not in self.client.playing_list:
                self.client.playing_list.append((player.summoner, player.tag))
                self.client.playing_list_ids[player.summoner] = player.discord_id
            await self.client.send_ready_list(message)


@dataclass
class Remove(Command):
    name: str = "remove"
    description: str = "Leave the lobby"
    usage: str = "!remove"
    example: str = "!remove"

    async def execute(self, message, *args):
        player = await User.get_by_discord_id(int(message.author.id))
        if (player.summoner, player.tag) in self.client.playing_list:
            self.client.playing_list.remove((player.summoner, player.tag))
            self.client.playing_list_ids.pop(player.summoner)
            await self.client.send_ready_list(message)
        else:
            await message.channel.send("You are not in the lobby.")


@dataclass
class Close(Command):
    name: str = "close"
    description: str = "Close the lobby"
    usage: str = "!close"
    example: str = "!close"

    async def execute(self, message, *args):
        if len(self.client.playing_list) < 10:
            await message.channel.send("You don't have enough players to play, you need at least 10")
        else:
            output_string = "Ready to play: \n"
            for index, player in enumerate(self.client.playing_list, start=1):
                output_string += "{}. {}\n".format(index, player[0])
            await message.channel.send(output_string)
            await message.channel.send("Starting the draw! Give me some seconds.")
            blue_team, red_team, ranks = await balance(self.client.playing_list)
            await message.channel.send(beautify_teams(blue_team, red_team, ranks, self.client.guilds[0].emojis))
            blue_team_channel = utils.get(self.client.guilds[0].channels, name="Team 1")
            red_team_channel = utils.get(self.client.guilds[0].channels, name="Team 2")
            for player in blue_team.get("players"):
                await (
                    self.client.guilds[0]
                    .get_member(int(self.client.playing_list_ids.get(player)))
                    .move_to(blue_team_channel)
                )
            for player in red_team.get("players"):
                await (
                    self.client.guilds[0]
                    .get_member(int(self.client.playing_list_ids.get(player)))
                    .move_to(red_team_channel)
                )


@dataclass
class Upload(Command):
    name: str = "upload"
    description: str = "Upload a screenshot to create a match"
    usage: str = "!upload"
    example: str = "!upload"
    image_recognition: ImageRecognition = field(default_factory=ImageRecognition)

    async def execute(self, message, *args):
        async with ClientSession() as session:
            async with session.get(message.attachments[0].url) as response:
                # Read the image as bytes
                image_bytes = await response.read()

                # Convert the bytes to a numpy array
                image_array = np.frombuffer(image_bytes, np.uint8)

                # Decode the image using OpenCV
                image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
                self.image_recognition.set_screenshot(image)
                champions = self.image_recognition.get_champions()
                await message.channel.send(f"Match created with champions: {', '.join(champions)}")