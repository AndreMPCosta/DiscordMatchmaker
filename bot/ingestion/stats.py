from functools import lru_cache
from typing import Any

import cv2
from cv2 import Mat
from dateparser import parse
import numpy as np
from numpy import array, dtype, ndarray
from PIL import Image, ImageEnhance
from rapidocr_onnxruntime import RapidOCR

from api.models.match import Match
from bot import get_project_root
from bot.ingestion.match import ImageRecognition
from bot.utils import remove_accents


@lru_cache
def get_engine() -> RapidOCR:
    return RapidOCR()


class OCR:
    def __init__(self, image: Mat | ndarray[Any, dtype] | ndarray | str):
        self.image_path = None
        if isinstance(image, str):
            self.image_path = image
        self.image = image

    def preprocess_image(self) -> ndarray:
        img = self.image if not isinstance(self.image, str) else Image.open(self.image)

        # Convert to grayscale
        img = img.convert("L")

        # Increase contrast
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(0.1)

        # Resize if necessary (optional)
        img = img.resize((img.width * 2, img.height * 2))

        # Convert to NumPy array
        img_array = array(img)

        return img_array

    def get_text(self) -> list[str]:
        self.change_team2_color()
        results, elapse = get_engine()(self.preprocess_image())
        text_list = []
        for result in results:
            for text in result:
                if isinstance(text, str):
                    text_list.append(text)
        return text_list

    def change_team2_color(self):
        # Load image using OpenCV for color processing
        img = self.image if not isinstance(self.image, str) else cv2.imread(self.image)

        # Define the color range for Team 2 (red team)
        lower_red = np.array([0, 0, 100])
        upper_red = np.array([50, 27, 255])

        # Find the red color in the image (Team 2's color)
        mask = cv2.inRange(img, lower_red, upper_red)

        # Change the red areas (Team 2) to a color similar to Team 1's color (blue team)
        img[mask > 0] = [255, 255, 255]  # Example: Change to white (adjust this as needed)

        # Convert the processed image back to PIL Image
        processed_img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))

        # Update the image attribute to the new processed image
        self.image = processed_img

    def create_match(self, summoner_name: str) -> Match:
        summoner_name = remove_accents(summoner_name)
        text_list = self.get_text()
        print(text_list)
        fields = {}
        find_custom = text_list.index("Custom")
        # Find all indexes of 'BANS'
        bans_objectives = [_index for _index, value in enumerate(text_list) if "BANS" in value]
        fields["duration"] = text_list[find_custom + 1]
        fields["date"] = parse(text_list[find_custom + 2])
        find_teams = [_index for _index, value in enumerate(text_list) if "TEAM" in value]
        for team in ["blue", "red"]:
            find_team = find_teams[0 if team == "blue" else 1]
            kills, deaths, assists = text_list[find_team + 1].replace("X", "").split("/")
            fields[f"{team}_team"] = {
                "stats": {
                    "kills": kills,
                    "deaths": deaths,
                    "assists": assists,
                    "total_gold": int(text_list[find_team + 2].replace(",", "")),
                },
            }
            fields[f"{team}_team"]["players"] = []
            sub_index = 0
            for index in range(0, 5):
                while True:
                    level = text_list[bans_objectives[0 if team == "blue" else 1] + 1 + sub_index + (index * 5)]
                    try:
                        level = int(level)
                        if 1 < level <= 18:
                            break
                        else:
                            sub_index += 1
                    except ValueError:
                        # get the digits from the string
                        level = "".join(i for i in level if i.isdigit())
                        if level != "":
                            if 1 < int(level) <= 18:
                                break
                        sub_index += 1
                while True:
                    name = text_list[bans_objectives[0 if team == "blue" else 1] + 2 + sub_index + (index * 5)]
                    if not name.isupper():
                        if not name.isdigit():
                            break
                    sub_index += 1
                fields[f"{team}_team"]["players"].append(
                    {
                        "name": name,
                        "picked_champion": None,
                        "stats": {
                            "level": level,
                            "kills": int(
                                text_list[
                                    bans_objectives[0 if team == "blue" else 1] + 3 + sub_index + (index * 5)
                                ].split("/")[0]
                            ),
                            "deaths": int(
                                text_list[
                                    bans_objectives[0 if team == "blue" else 1] + 3 + sub_index + (index * 5)
                                ].split("/")[1]
                            ),
                            "assists": int(
                                text_list[
                                    bans_objectives[0 if team == "blue" else 1] + 3 + sub_index + (index * 5)
                                ].split("/")[2]
                            ),
                            "minions_killed": int(
                                text_list[bans_objectives[0 if team == "blue" else 1] + 4 + sub_index + (index * 5)]
                            ),
                            "gold_earned": float(
                                text_list[
                                    bans_objectives[0 if team == "blue" else 1] + 5 + sub_index + (index * 5)
                                ].replace(",", "")
                            ),
                        },
                    }
                )
                if index == 3:
                    catch_string = ""
                    catch_index = 0
                    while len(catch_string) < 6:
                        catch_string += text_list[
                            bans_objectives[0 if team == "blue" else 1] + 6 + sub_index + catch_index + (index * 5)
                        ]
                        catch_index += 1
                    (
                        towers_destroyed,
                        inhibitors_destroyed,
                        barons_slain,
                        dragons_slain,
                        rift_heralds_slain,
                        void_grubs_slain,
                    ) = map(int, catch_string)
                    fields[f"{team}_team"]["stats"].update(
                        {
                            "towers_destroyed": towers_destroyed,
                            "inhibitors_destroyed": inhibitors_destroyed,
                            "barons_slain": barons_slain,
                            "dragons_slain": dragons_slain,
                            "rift_heralds_slain": rift_heralds_slain,
                            "void_grubs_slain": void_grubs_slain,
                        }
                    )
        img_recognition = ImageRecognition()
        img_recognition.set_screenshot(cv2.imread(self.image_path) if self.image_path else self.image)
        champions = img_recognition.get_champions()
        for team in ["blue", "red"]:
            for player in fields[f"{team}_team"]["players"]:
                player["picked_champion"] = champions.pop(0)
        label_winning = "victory" if "victory".upper() in text_list else "defeat"
        if summoner_name in [player["name"] for player in fields["blue_team"]["players"]]:
            fields["winner"] = "blue" if label_winning == "victory" else "red"
        print(fields)
        return Match(**fields)


if __name__ == "__main__":
    ocr = OCR(f"{get_project_root()}/tests/data/test12.png")
    ocr.create_match("PretinhoDaGuiné")
