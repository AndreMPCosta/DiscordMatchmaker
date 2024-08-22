from functools import lru_cache
from typing import Any

from cv2 import Mat
from numpy import array, dtype, ndarray
from PIL import Image, ImageEnhance
from rapidocr_onnxruntime import RapidOCR

from bot import get_project_root


@lru_cache
def get_engine() -> RapidOCR:
    return RapidOCR()


class OCR:
    def __init__(self, image: Mat | ndarray[Any, dtype] | ndarray | str):
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
        results, elapse = get_engine()(self.preprocess_image())
        text_list = []
        for result in results:
            for text in result:
                if isinstance(text, str):
                    text_list.append(text)
        return text_list

    def create_match(self):
        # text_list = self.get_text()
        fields = {}
        text_list = [
            "172",
            "RLoR",
            "PLAY",
            "HOME",
            "TFT",
            "30.4K",
            "DEFEAT",
            "Summoner's Rift",
            "Custom",
            "27:07",
            "08/16/2024",
            "GameID",
            "SCOREBOARD",
            "OVERVIEW",
            "STATS",
            "GRAPHS",
            "RUNES",
            "TEAM 1",
            "28/31/28",
            "54,539",
            "BANS + OBJECTIVES",
            "黄图15",
            "PretinhoDaGuine",
            "3/7/6",
            "221",
            "11,712",
            "化器",
            "15",
            "Filipados",
            "7/5/10",
            "167",
            "11,210",
            "14",
            "TEAORXO",
            "flemsss",
            "11/6/2",
            "232",
            "13,607",
            "OOAAOA",
            "10",
            "Mazzeee",
            "2/5/8",
            "20",
            "7,474",
            "600200",
            "美14",
            "CrazedAfro",
            "5/8/2",
            "188",
            "10,536",
            "CEA",
            "56,402",
            "BANS + OBJECTIVES",
            "15",
            "Sinj",
            "6/7/8",
            "168",
            "10,939",
            "17",
            "sirGOD",
            "10/3/3",
            "238",
            "13,519",
            "14",
            "madafz",
            "5/5/8",
            "193",
            "11,092",
            "15",
            "locked in",
            "9/5/13",
            "151",
            "12,985",
            "7",
            "1",
            "1103",
            "12",
            "Homem do Saco",
            "1/8/15",
            "16",
            "7,867",
        ]

        find_custom = text_list.index("Custom")
        # Find all indexes of 'Custom'
        bans_objectives = [index for index, value in enumerate(text_list) if value == "BANS + OBJECTIVES"]
        fields["duration"] = text_list[find_custom + 1]
        fields["date"] = text_list[find_custom + 2]
        for team in ["blue", "red"]:
            find_team = text_list.index("TEAM 1" if team == "blue" else "TEAM 2")
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
                if index != 4:
                    level = "".join(
                        [
                            char
                            for char in text_list[
                                bans_objectives[0 if team == "blue" else 1] + 1 + sub_index + (index * 5)
                            ]
                            if char.isdigit()
                        ]
                    )
                    while not level:
                        sub_index += 1
                        level = "".join(
                            [
                                char
                                for char in text_list[bans_objectives[0 if team == "blue" else 1] + 1 + (index * 5) + 1]
                                if char.isdigit()
                            ]
                        )
                    fields[f"{team}_team"]["players"].append(
                        {
                            "name": text_list[
                                bans_objectives[0 if team == "blue" else 1] + 2 + sub_index + (index * 5)
                            ],
                            "picked_champion": None,
                            "stats": {
                                "level": int(level),
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
            fields[f"{team}_team"]["players"].append(
                {
                    "name": text_list[bans_objectives[0 if team == "blue" else 1] + 8 + (index * 5)],
                    "picked_champion": None,
                    "stats": {
                        "level": int(text_list[bans_objectives[0 if team == "blue" else 1] + 7 + (index * 5)]),
                        "kills": int(
                            text_list[bans_objectives[0 if team == "blue" else 1] + 9 + (index * 5)].split("/")[0]
                        ),
                        "deaths": int(
                            text_list[bans_objectives[0 if team == "blue" else 1] + 9 + (index * 5)].split("/")[1]
                        ),
                        "assists": int(
                            text_list[bans_objectives[0 if team == "blue" else 1] + 9 + (index * 5)].split("/")[2]
                        ),
                        "minions_killed": int(
                            text_list[bans_objectives[0 if team == "blue" else 1] + 10 + (index * 5)]
                        ),
                        "gold_earned": float(
                            text_list[bans_objectives[0 if team == "blue" else 1] + 11 + (index * 5)].replace(",", "")
                        ),
                    },
                }
            )
        print(fields)


if __name__ == "__main__":
    ocr = OCR(f"{get_project_root()}/tests/data/test13.png")
    print(ocr.get_text())
    # print(ocr.create_match())
