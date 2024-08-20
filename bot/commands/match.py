from dataclasses import dataclass

from bot.commands import Command


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
