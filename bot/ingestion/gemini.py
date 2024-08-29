from io import BytesIO
from json import loads
from logging import getLogger
from os import environ
from typing import TYPE_CHECKING

from aiofiles import open as async_open
from discord import Message
from dotenv import load_dotenv
from google.api_core.exceptions import InternalServerError
import google.generativeai as genai
from PIL import Image

from api.consts import Champion
from api.models.match import MatchDocument
from bot import get_project_root
from bot.consts import matches_folder
from bot.exceptions import GeminiError
from bot.ingestion.match import ImageRecognition

load_dotenv()
genai.configure(api_key=environ.get("GOOGLE_API_KEY"))
model = genai.GenerativeModel(model_name="gemini-1.5-pro")

logger = getLogger("gemini")

if TYPE_CHECKING:
    from bot.client import MatchMaker


async def save_image(path: str, image: memoryview) -> None:
    async with async_open(path, "wb") as file:
        await file.write(image)


async def create_match(
    client: "MatchMaker",
    image: Image,
    champions: list[Champion | None],
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
    try:
        response = model.generate_content([prompt, image])
    except InternalServerError:
        new_model = genai.GenerativeModel(model_name="gemini-1.5-flash")
        try:
            print("Trying to fetch match info with flash model")
            response = new_model.generate_content([prompt, image])
        except InternalServerError:
            raise GeminiError()
    logger.info("Match info fetched")
    filtered_response = response.text.replace("```json", "").replace("```", "")
    json_response = loads(filtered_response)
    # Convert all keys in the dictionary to lowercase for case-insensitive lookup
    lowercase_playing_list_ids = {k.lower(): v for k, v in client.playing_list_ids.items()}
    for team in ["blue", "red"]:
        for player in json_response[f"{team}_team"]["players"]:
            player["discord_id"] = lowercase_playing_list_ids.get(player["name"].lower())
            player["picked_champion"] = champions.pop(0)
    match = MatchDocument(**json_response)
    if send_match_details:
        await match.send_match_details(message)
    match.blue_team.bans = []
    match.red_team.bans = []
    await match.save()
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    await save_image(f"{matches_folder}/{str(match.id)}.png", buffer.getbuffer())
    client.last_match = match
    return match


if __name__ == "__main__":
    from asyncio import run

    from cv2 import imread

    from bot.mock.client import MockClient

    image_recognition = ImageRecognition()
    image_recognition.set_screenshot(imread(f"{get_project_root()}/tests/data/test13.png"))
    _champions = image_recognition.get_champions()
    _client = MockClient()
    run(create_match(_client, Image.open(f"{get_project_root()}/tests/data/test13.png"), _champions))
