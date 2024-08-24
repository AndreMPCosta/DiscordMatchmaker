from os import getenv

from dotenv import load_dotenv

from bot.client import client

if __name__ == "__main__":
    load_dotenv()

    client.run(getenv("TOKEN"))
