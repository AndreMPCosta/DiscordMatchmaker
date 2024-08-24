from json import loads
from logging import getLogger
from os import environ
from pprint import pprint

from dotenv import load_dotenv
import google.generativeai as genai
from PIL import Image

from api.models.match import Match
from bot import get_project_root

load_dotenv()
genai.configure(api_key=environ.get("GOOGLE_API_KEY"))
model = genai.GenerativeModel(model_name="gemini-1.5-pro")

logger = getLogger("gemini")


def create_match(
    playing_list: list[tuple[str, str]],
    image: Image,
    champions: list[str],
) -> Match:
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
    {[summoner for summoner, tag in playing_list]}\n
    """
    logger.info("Trying to fetch match info")
    response = model.generate_content([prompt, image])
    logger.info("Match info fetched")
    filtered_response = response.text.replace("```json", "").replace("```", "")
    json_response = loads(filtered_response)
    for team in ["blue", "red"]:
        for player in json_response[f"{team}_team"]["players"]:
            player["picked_champion"] = champions.pop(0)
    return Match(**json_response)


if __name__ == "__main__":
    _match = create_match(
        playing_list=[
            ("PretinhoDaGuiné", "EUW"),
            ("Elesh95", "EUW"),
            ("Toy", "2228"),
            ("popping off", "EUW"),
            ("Mazzeee", "EUW"),
            ("locked in", "EUW"),
            ("zau", "EUW"),
            ("salganhadaa", "SIMOR"),
            ("Filipados", "EUW"),
            ("Cardoso00", "EUW"),
        ],
        image=Image.open(f"{get_project_root()}/tests/data/test10.png"),
        champions=["Gragas", "Thresh", "Khazix", "Yasuo", "Kaisa", "Lux", "Blitzcrank", "Caitlyn", "Lillia", "Wukong"],
    )
    pprint(_match)
