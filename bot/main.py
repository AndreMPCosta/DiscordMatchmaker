from json import dump
from os import getenv, mkdir
from os.path import exists, normpath

from dotenv import load_dotenv

from bot.client import client
from bot.consts import data_folder

if __name__ == "__main__":
    load_dotenv()
    if not exists(data_folder):
        mkdir(data_folder)
    if not exists(normpath(f"{data_folder}/db.json")):
        print("Data folder created")
        with open(normpath(f"{data_folder}/db.json"), "w") as file:
            dump({"players": {}, "last_refresh": None, "build_id": None}, file, indent=4)

    client.run(getenv("TOKEN"))
