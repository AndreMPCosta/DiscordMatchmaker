from os import getenv, mkdir
from os.path import exists

from dotenv import load_dotenv

from bot.client import client
from bot.consts import data_folder, matches_folder

if __name__ == "__main__":
    load_dotenv()
    if not exists(data_folder):
        mkdir(data_folder)
    if not exists(matches_folder):
        mkdir(matches_folder)

    client.run(getenv("TOKEN"))
