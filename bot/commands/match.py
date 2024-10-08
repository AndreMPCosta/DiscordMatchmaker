from asyncio import Task, create_task
from dataclasses import dataclass, field
from logging import getLogger
from os import environ

from aiohttp import ClientSession
import cv2
from discord import File, Message, utils
import numpy as np
from PIL import Image

from api.consts import Champion
from api.models.match import MatchDocument
from api.models.user import User
from bot import get_project_root
from bot.commands import Command
from bot.commands.post_match import show_mvp
from bot.exceptions import GeminiError
from bot.helpers import balance, beautify_teams
from bot.ingestion.gemini import create_match
from bot.ingestion.match import ImageRecognition

logger = getLogger("discord.client")


@dataclass
class Playlist(Command):
    name: str = "playlist"
    description: str = "Show the current lobby"
    usage: str = "!playlist"
    example: str = "!playlist"

    async def execute(self, message: Message, *args):
        await self.client.send_ready_list(message)


@dataclass
class Reset(Command):
    name: str = "reset"
    description: str = "Reset the lobby playing list"
    usage: str = "!reset"
    example: str = "!reset"

    async def execute(self, message: Message, *args):
        self.client.playing_list = []
        self.client.playing_list_ids = {}
        create_task(self.update_redis_playing_list())
        await message.channel.send("Lobby has been reset.")


@dataclass
class Play(Command):
    name: str = "play"
    description: str = "Join the lobby"
    usage: str = "!play"
    example: str = "!play"

    async def execute(self, message: Message, *args):
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
                create_task(self.update_redis_playing_list())
            else:
                await message.channel.send("You are already in the lobby.")
                return
            await self.client.send_ready_list(message)


@dataclass
class Remove(Command):
    name: str = "remove"
    description: str = "Leave the lobby"
    usage: str = "!remove"
    example: str = "!remove"

    async def execute(self, message: Message, *args):
        player = await User.get_by_discord_id(int(message.author.id))
        if (player.summoner, player.tag) in self.client.playing_list:
            self.client.playing_list.remove((player.summoner, player.tag))
            self.client.playing_list_ids.pop(player.summoner)
            create_task(self.update_redis_playing_list())
            await self.client.send_ready_list(message)
        else:
            await message.channel.send("You are not in the lobby.")


@dataclass
class Close(Command):
    name: str = "close"
    description: str = "Close the lobby"
    usage: str = "!close"
    example: str = "!close"

    async def execute(self, message: Message, *args):
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
            blue_team_channel = utils.get(
                self.client.guilds[0].channels, name=environ.get("BLUE_TEAM_CHANNEL", "Team 1")
            )
            red_team_channel = utils.get(self.client.guilds[0].channels, name=environ.get("RED_TEAM_CHANNEL", "Team 2"))
            for player in blue_team.get("players"):
                try:
                    await (
                        self.client.guilds[0]
                        .get_member(int(self.client.playing_list_ids.get(player[0])))
                        .move_to(blue_team_channel)
                    )
                except TypeError:
                    logger.error(f"Player {player} could not be moved to the blue team channel")
            for player in red_team.get("players"):
                try:
                    await (
                        self.client.guilds[0]
                        .get_member(int(self.client.playing_list_ids.get(player[0])))
                        .move_to(red_team_channel)
                    )
                except TypeError:
                    logger.error(f"Player {player} could not be moved to the red team channel")


@dataclass
class Upload(Command):
    name: str = "upload"
    description: str = (
        "Upload a screenshot to create a match, "
        "please capture between starting on (0,0) coordinates "
        "of the client and end before reaching the friends list, "
        "so you can see until the bans + objectives"
    )
    usage: str = "!upload"
    example: str = "!upload"
    image_recognition: ImageRecognition = field(default_factory=ImageRecognition)

    async def execute(self, message: Message, *args):
        async with ClientSession() as session:
            async with session.get(message.attachments[0].url) as response:
                # Read the image as bytes
                image_bytes = await response.read()

                # Convert the bytes to a numpy array
                image_array = np.frombuffer(image_bytes, np.uint8)

                # Decode the image using OpenCV
                image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)
                await message.channel.send("Processing image, this may take a few seconds...")
                self.image_recognition.set_screenshot(image)
                champions = self.image_recognition.get_champions()
                if champions is not None:
                    # Run create_match in a background task
                    task: Task = create_task(self.run_create_match(image, champions, message))
                    # Notify when the task is completed
                    task.add_done_callback(lambda t: create_task(self.on_task_complete(t, message)))

    async def run_create_match(
        self, image: np.ndarray, champions: list[Champion | None], message: Message
    ) -> MatchDocument:
        try:
            # Run the create_match function asynchronously
            result: MatchDocument = await create_match(self.client, Image.fromarray(image), champions, True, message)
            return result
        except (Exception, GeminiError) as e:
            # Handle exceptions and notify user
            await message.channel.send(f"An error occurred while creating the match: {e}")

    async def on_task_complete(self, task: Task, message: Message) -> None:
        try:
            match: MatchDocument = task.result()
            if match:
                winning_team = match.blue_team if match.winner == "blue" else match.red_team
                self.client.eligible_mvps = winning_team.players
                await show_mvp(self.client, message)
            else:
                await message.channel.send("Failed to create match.")
        except (Exception,) as e:
            await message.channel.send(f"An error occurred after processing: {e}")

    async def show_help(self, message: Message):
        description = self.description
        usage = self.usage
        example = f"\n{self.example}" if self.example != self.usage else None
        _message = f"{description}\n" f"Usage: {usage}{f'Example: {example}' if example else ''}"
        await message.channel.send(_message, file=File(f"{get_project_root()}/bot/commands/assets/sample.png"))
