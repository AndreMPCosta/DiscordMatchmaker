from dataclasses import dataclass
from datetime import datetime
from logging import getLogger

from discord import Message

from api.models.user import User
from bot.commands import Command
from bot.exceptions import SummonerNotFound
from bot.scrapper import get_rank_v2

logger = getLogger(__name__)


@dataclass
class Register(Command):
    name: str = "register"
    description: str = "Register a summoner name"
    usage: str = "!register <summoner>#<tag>"
    example: str = "!register Faker#EUW"

    async def execute(self, message: Message, *args):
        updated = False
        author_id = int(message.author.id)
        user = await User.get_by_discord_id(author_id)
        summoner = " ".join(*args)
        # find the # char
        if "#" in summoner:
            summoner, tag = summoner.split("#")
        else:
            tag = "EUW"
        try:
            await get_rank_v2(summoner, tag)
        except SummonerNotFound as e:
            await message.channel.send(e.detail)
            return
        if not user:
            user = User(discord_id=author_id, summoner=summoner, tag=tag)
        else:
            updated = True
            user.summoner = summoner
            user.tag = tag
            user.last_modified = datetime.utcnow()
        await user.save()

        logger.info(
            f"Username '{summoner}' and Tag '{tag}' successfully "
            f"{'registered' if not updated else 'updated'}, tied to {message.author.name}"
        )
        await message.channel.send(
            f"Username '{summoner}' and Tag '{tag}' successfully "
            f"{'registered' if not updated else 'updated'}, tied to {message.author.name}"
        )
