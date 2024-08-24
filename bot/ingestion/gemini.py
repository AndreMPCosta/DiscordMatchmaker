from json import loads
from logging import getLogger
from os import environ
from typing import TYPE_CHECKING

from discord import Message
from dotenv import load_dotenv
import google.generativeai as genai
from PIL import Image

from api.models.match import MatchDocument

load_dotenv()
genai.configure(api_key=environ.get("GOOGLE_API_KEY"))
model = genai.GenerativeModel(model_name="gemini-1.5-pro")

logger = getLogger("gemini")


if TYPE_CHECKING:
    from bot.client import MatchMaker


async def create_match(
    client: "MatchMaker",
    image: Image,
    champions: list[str],
    send_match_details: bool = False,
    message: Message | None = None,
) -> MatchDocument:
    prompt = f"""
    Based on this classes:\n
    class PlayerStats(BaseModel):
        kills: int
        deaths: int
        assists: int
        minions_killed: int
        gold_earned: int
        level: int
    \n
    class TeamStats(BaseModel):
        kills: int
        deaths: int
        assists: int
        total_gold: int
        towers_destroyed: int
        inhibitors_destroyed: int
        barons_slain: int
        dragons_slain: int
        rift_heralds_slain: int
        void_grubs_slain: int
    \n
    class Player(BaseModel):
        name: str
        stats: PlayerStats
    \n
    class Team(BaseModel):
        players: list[Player]
        bans: list[str] = Field(default_factory=list)
        stats: TeamStats
    \n
    class Match(BaseModel):
        blue_team: Team
        red_team: Team
        duration: str
        date: datetime
        winner: Literal["blue", "red"]
    Create me a json reflecting the image I just gave you.\n
    Bear in mind these are the players names (not ordered): \n
    {[summoner for summoner, tag in client.playing_list]}\n
    """
    logger.info("Trying to fetch match info")
    response = model.generate_content([prompt, image])
    logger.info("Match info fetched")
    filtered_response = response.text.replace("```json", "").replace("```", "")
    json_response = loads(filtered_response)
    for team in ["blue", "red"]:
        for player in json_response[f"{team}_team"]["players"]:
            player["discord_id"] = client.playing_list_ids.get(player["name"])
            player["picked_champion"] = champions.pop(0)
    match = MatchDocument(**json_response)
    if send_match_details:
        await match.send_match_details(message)
    await match.save()
    client.last_match = match
    return match
