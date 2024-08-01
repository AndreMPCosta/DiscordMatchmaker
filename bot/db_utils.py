from json import load, dump
from os.path import normpath
from timeit import default_timer

from bot.consts import data_folder


def load_json() -> dict[str, dict | float | str]:
    with open(normpath(f'{data_folder}/db.json'), 'r') as file:
        json = load(file)
        if not json.get('players'):
            json['players'] = {}
        return json


def update_build_id(build_id: str):
    json: dict[str, dict | float | str] = load_json()
    json['last_refresh'] = default_timer()
    json['build_id'] = build_id
    with open(normpath(f'{data_folder}/db.json'), 'w') as file:
        dump(json, file, indent=4)


def register_player(summoner: str, discord_id: str, tag: str = "euw"):
    json: dict[str, dict] = load_json()

    if discord_id in json["players"]:
        json["players"][discord_id]["summoner"] = summoner
        json["players"][discord_id]["tag"] = tag
    else:
        json["players"][discord_id] = {"summoner": summoner, "tag": tag}

    with open(normpath(f'{data_folder}/db.json'), 'w') as file:
        dump(json, file, indent=4)
