from dataclasses import dataclass

from discord import Message

from bot.commands import Command


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

    async def check_vote(self, message: Message, player: int, voter: int):
        if not 10 > player > 0:
            await message.channel.send(f"Invalid player number: {player}")
        elif sum(self.client.mvp_votes) == 10:
            await message.channel.send(
                f"You can't vote anymore, the winner of this round is {self.client.last_match.mvp}"
            )
        elif len(self.client.playing_list) < 10:
            await message.channel.send("The game did not start yet.")
        elif voter in self.client.voters:
            await message.channel.send("You already voted.")
        if self.client.playing_list_ids.get(self.client.playing_list[player][0]) not in [
            player.discord_id
            for player in getattr(self.client.last_match, f"{self.client.last_match.winner}_team").players
        ]:
            await message.channel.send(f"Player {self.client.playing_list[player][0]} is not in the winning team.")
