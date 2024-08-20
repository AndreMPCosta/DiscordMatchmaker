from dataclasses import dataclass

from bot.commands import Command


@dataclass
class Help(Command):
    name: str = "help"
    description: str = "List all commands"
    usage: str = "!help"
    example: str = "!help"

    async def execute(self, message, *args):
        output_string = "```"
        for command in vars(self.client.commands).values():
            output_string += f"!{command.name}: {command.description}\n"
        output_string += "For more information on a command, type !help <command>\n"
        output_string += "```"
        await message.channel.send(output_string)
