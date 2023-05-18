from json import dump
from os import mkdir, getenv
from os.path import exists, normpath
from typing import Any
from discord import Client, Intents
from dotenv import load_dotenv
from bot.consts import data_folder
from bot.db_utils import load_json, register_player
from bot.helpers import balance, beautify_teams


class MatchMaker(Client):
    def __init__(self, *, intents: Intents, **options: Any):
        super().__init__(intents=intents, **options)
        self.playing_list = set()
        self.players = load_json().get('players')

    def refresh_players(self):
        self.players = load_json().get('players')

    async def on_ready(self):
        print(f'Logged on as {self.user}!')

    async def on_message(self, message):
        # we do not want the bot to reply to itself
        if message.author.id == self.user.id:
            return

        content = message.content
        author_id = str(message.author.id)
        match content.split():
            case ["!ping"]:
                await message.channel.send('pong')
            case ["!reset"]:
                self.playing_list = set()
            case ["!playlist"]:
                output_string = 'Ready to play: \n'
                for player in enumerate(self.playing_list, start=1):
                    output_string += '{}. {}\n'.format(*player)
                await message.channel.send(output_string)
            case ["!register", *summoner]:
                summoner = ' '.join(summoner)
                register_player(summoner, author_id)
                self.refresh_players()
                await message.channel.send(
                    f"Username '{summoner}' successfully registered, tied to {message.author.name}"
                )
            case ["!play"]:
                if len(self.playing_list) == 10:
                    await message.channel.send('The lobby is full.')
                else:
                    output_string = 'Ready to play: \n'
                    player = self.players.get(author_id)
                    if not player:
                        await message.channel.send('You are not registered, please register first.')
                    self.playing_list.add(player.get('summoner'))
                    for player in enumerate(self.playing_list, start=1):
                        output_string += '{}. {}\n'.format(*player)
                    await message.channel.send(output_string)
            case ["!close"]:
                if len(self.playing_list) < 10:
                    await message.channel.send("You don't have enough players to play, you need at least 10")
                else:
                    output_string = 'Ready to play: \n'
                    for player in enumerate(self.playing_list, start=1):
                        output_string += '{}. {}\n'.format(*player)
                    await message.channel.send(output_string)
                    await message.channel.send('Starting the draw! Give me some seconds.')
                    blue_team, red_team, ranks = await balance(self.playing_list)
                    await message.channel.send(beautify_teams(blue_team, red_team, ranks, self.guilds[0].emojis))


if __name__ == '__main__':
    load_dotenv()
    if not exists(data_folder):
        mkdir(data_folder)
    if not exists(normpath(f'{data_folder}/db.json')):
        print('Data folder created')
        with open(normpath(f'{data_folder}/db.json'), 'w') as file:
            dump({'players': {}, 'last_refresh': None, 'build_id': None}, file, indent=4)
    _intents = Intents.default()
    _intents.message_content = True

    client = MatchMaker(intents=_intents)
    client.run(getenv('TOKEN'))
