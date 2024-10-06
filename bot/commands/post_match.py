from collections import Counter
from dataclasses import dataclass
from os import environ
from random import randint
from typing import TYPE_CHECKING

from discord import Message, utils

from api.models.match import MVP, Player
from bot.commands import Command

if TYPE_CHECKING:
    from bot.client import MatchMaker


async def show_mvp(
    client: "MatchMaker",
    message: Message,
):
    output_string = "MVP list: \n"
    for index, player in enumerate(client.eligible_mvps, start=1):
        output_string += f"{index}. {player.name} ({list(client.mvp_votes.values()).count(player)})\n"
    await message.channel.send(output_string)


@dataclass
class Vote(Command):
    name: str = "vote"
    description: str = "Vote for the mvp player"
    usage: str = "!vote <player>"
    example: str = "!vote 1"

    async def execute(self, message: Message, *args):
        player, voter = args
        if isinstance(player, list):
            player = int(player[0])
        is_valid = await self.check_vote(message, player, voter)
        if is_valid:
            await self.vote(message, player, voter)

    async def finalize(self):
        lobby_channel = utils.get(self.client.guilds[0].channels, name=environ.get("LOBBY_CHANNEL", "Lobby"))
        for discord_id in self.client.playing_list_ids.values():
            await self.client.guilds[0].get_member(int(discord_id)).move_to(lobby_channel)
        self.client.last_match = None
        self.client.last_match_id = None
        self.client.mvp_votes = dict()
        self.client.eligible_mvps = []
        self.client.playing_list = []
        self.client.playing_list_ids = {}

    def get_most_common_ids_and_votes(self) -> tuple[list[Player], int]:
        # Count the occurrences of each ID in the list of values
        counter = Counter(self.client.mvp_votes.values())

        # Get the highest count (most common occurrence)
        highest_count = counter.most_common(1)[0][1]

        # Find all values with the highest count
        most_common_ids = [value for value, count in counter.items() if count == highest_count]

        return most_common_ids, highest_count

    async def vote(self, message: Message, player: int, voter: int):
        match = self.client.last_match
        self.client.mvp_votes[voter] = self.client.eligible_mvps[player - 1]
        if len(self.client.mvp_votes) == 10:
            mvps, votes = self.get_most_common_ids_and_votes()
            if len(mvps) > 1:
                await message.channel.send("There is a tie! Please vote again.")
                self.client.mvp_votes = {}
                self.client.eligible_mvps = mvps
                await show_mvp(self.client, message)
                return
            mvp = mvps[0]
            match.mvp = MVP(name=mvp.name, discord_id=mvp.discord_id, votes=votes)
            await match.save()
            await message.channel.send(
                f"All votes are in! The winner is: {self.client.eligible_mvps[player - 1].name} ({votes}) 🏆!"
            )
            await self.finalize()

    async def check_vote(self, message: Message, player: int, voter: int) -> bool:
        if not self.client.last_match:
            await message.channel.send("The game did not start yet.")
            return False
        elif not len(self.client.eligible_mvps) + 1 > player > 0:
            await message.channel.send(f"Invalid player number: {player}")
            return False
        elif len(self.client.mvp_votes) == 10:
            await message.channel.send(
                f"You can't vote anymore, the winner of this round is {self.client.last_match.mvp}"
            )
            return False
        elif voter in self.client.mvp_votes:
            await message.channel.send("You already voted.")
            return False
        elif voter not in [player.discord_id for player in self.client.last_match.blue_team.players] + [
            player.discord_id for player in self.client.last_match.red_team.players
        ]:
            await message.channel.send("You are not in this game.")
            return False
        return True


@dataclass
class ForceVote(Command):
    name: str = "force_vote"
    description: str = "Force the mvp vote (only available for admins)"
    usage: str = "!force_vote <player>"
    example: str = "!force_vote 2"

    async def execute(self, message: Message, *args):
        player = args[0]
        if not self.client.last_match:
            await message.channel.send("The game did not start yet.")
        elif "Admin".lower() not in [role.name.lower() for role in message.author.roles]:
            await message.channel.send("You don't have permission to force the vote.")
        elif not len(self.client.eligible_mvps) + 1 > player > 0:
            await message.channel.send(f"Invalid player number: {player}")
        self.client.commands.vote.vote(message, player, randint(10**17, 10**18 - 1))


@dataclass
class ShowMissing(Command):
    name: str = "show_missing"
    description: str = "Show the missing votes"
    usage: str = "!show_missing"
    example: str = "!show_missing"

    async def execute(self, message: Message, *args):
        if not self.client.last_match:
            await message.channel.send("The game did not start yet.")
            return
        missing_votes = [
            player
            for player in self.client.last_match.blue_team.players + self.client.last_match.red_team.players
            if player.discord_id not in self.client.mvp_votes
        ]
        output_string = "Missing votes: \n"
        for index, player in enumerate(missing_votes, start=1):
            output_string += f"{index}. {player.name}\n"
        await message.channel.send(output_string)


@dataclass
class MVPList(Command):
    name: str = "mvp"
    description: str = "Show the MVP list"
    usage: str = "!mvp"
    example: str = "!mvp"

    async def execute(self, message: Message, *args):
        await show_mvp(self.client, message)
