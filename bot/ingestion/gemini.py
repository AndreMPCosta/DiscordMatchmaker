from json import loads
from os import environ

from dotenv import load_dotenv
import google.generativeai as genai
import PIL.Image

from api.models.match import Match
from api.utils import get_project_root

load_dotenv()
genai.configure(api_key=environ.get("GOOGLE_API_KEY"))
img = PIL.Image.open(f"{get_project_root()}/tests/data/test11.png")

model = genai.GenerativeModel(model_name="gemini-1.5-pro")
prompt = """
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
[]\n
"""

response = model.generate_content([prompt, img])
print(response.text)
filtered_response = response.text.replace("```json", "").replace("```", "")
match = Match(**loads(filtered_response))
print(match)
