from collections import Counter
from dataclasses import dataclass
from typing import TYPE_CHECKING

from discord import Message

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
        await self.check_vote(message, player, voter)

    def finalize(self):
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

    async def check_vote(self, message: Message, player: int, voter: int):
        if not len(self.client.eligible_mvps) + 1 > player > 0:
            await message.channel.send(f"Invalid player number: {player}")
        elif len(self.client.mvp_votes) == 10:
            await message.channel.send(
                f"You can't vote anymore, the winner of this round is {self.client.last_match.mvp}"
            )
        elif not self.client.last_match:
            await message.channel.send("The game did not start yet.")
        elif voter in self.client.mvp_votes:
            await message.channel.send("You already voted.")
        elif voter not in self.client.last_match.blue_team.players + self.client.last_match.red_team.players:
            await message.channel.send("You are not in this game.")
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
            self.finalize()


@dataclass
class MVPList(Command):
    name: str = "mvp"
    description: str = "Show the MVP list"
    usage: str = "!mvp"
    example: str = "!mvp"

    async def execute(self, message: Message, *args):
        await show_mvp(self.client, message)
