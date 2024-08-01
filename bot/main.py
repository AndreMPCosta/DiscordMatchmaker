from json import dump
from os import mkdir, getenv
from os.path import exists, normpath
from typing import Any
from discord import Client, Intents, utils
from dotenv import load_dotenv
from bot.consts import data_folder
from bot.db_utils import load_json, register_player
from bot.helpers import balance, beautify_teams


class MatchMaker(Client):
    def __init__(self, *, intents: Intents, **options: Any):
        super().__init__(intents=intents, **options)
        self.playing_list = []
        # [
        #     ("NinaKravitzzz", "EUW"),
        #     ("Sir Silv Slayer", "SIR"),
        #     ("CFortes", "EUW"),
        #     ("sinj", "sinji"),
        #     ("flemsss", "EUW"),
        #     ("salganhadaa", "simor"),
        #     ("zau", "EUW"),
        #     ("Elesh95", "EUW"),
        #     ("madafz", "EUW"),
        #     ("Princess RS", "EUW")
        # ]
        self.playing_list_ids = {}
        self.players = load_json().get('players')

    async def send_ready_list(self, message):
        output_string = 'Ready to play: \n'
        for index, player in enumerate(self.playing_list, start=1):
            output_string += '{}. {}\n'.format(index, player[0]) \
                if player[0] != len(self.playing_list) else '{}. {}'.format(index, player[0])
        await message.channel.send(output_string)

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
                self.playing_list = []
                self.playing_list_ids = {}
            case ["!playlist"]:
                await self.send_ready_list(message)
            case ["!register", *summoner]:
                summoner = ' '.join(summoner)
                # find the # char
                if '#' in summoner:
                    summoner, tag = summoner.split('#')
                else:
                    tag = 'euw'
                register_player(summoner, author_id, tag)
                self.refresh_players()
                await message.channel.send(
                    f"Username '{summoner}' and Tag '{tag}' successfully registered, tied to {message.author.name}"
                )
            case ["!play"]:
                if len(self.playing_list) == 10:
                    await message.channel.send('The lobby is full.')
                else:
                    player = self.players.get(author_id)
                    if not player:
                        await message.channel.send('You are not registered, please register first.')
                        return
                    elif (player.get('summoner'), player.get('tag')) not in self.playing_list:
                        self.playing_list.append((player.get('summoner'), player.get('tag')))
                        self.playing_list_ids[player.get('summoner')] = author_id
                    await self.send_ready_list(message)
            case ["!remove"]:
                player = self.players.get(author_id)
                if (player.get('summoner'), player.get('tag')) in self.playing_list:
                    self.playing_list.remove((player.get('summoner'), player.get('tag')))
                    self.playing_list_ids.pop(player.get('summoner'))
                    await self.send_ready_list(message)
            case ["!close"]:
                if len(self.playing_list) < 10:
                    await message.channel.send("You don't have enough players to play, you need at least 10")
                else:
                    output_string = 'Ready to play: \n'
                    for index, player in enumerate(self.playing_list, start=1):
                        output_string += '{}. {}\n'.format(index, player[0])
                    await message.channel.send(output_string)
                    await message.channel.send('Starting the draw! Give me some seconds.')
                    blue_team, red_team, ranks = await balance(self.playing_list)
                    await message.channel.send(beautify_teams(blue_team, red_team, ranks, self.guilds[0].emojis))
                    blue_team_channel = utils.get(self.guilds[0].channels, name='Team 1')
                    red_team_channel = utils.get(self.guilds[0].channels, name='Team 2')
                    # for player in blue_team.get('players'):
                    #     await self.guilds[0].get_member(int(self.playing_list_ids.get(player))).move_to(
                    #         blue_team_channel)
                    # for player in red_team.get('players'):
                    #     await self.guilds[0].get_member(int(self.playing_list_ids.get(player))).move_to(
                    #         red_team_channel)


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
