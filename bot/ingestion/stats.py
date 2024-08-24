from asyncio import run
from functools import lru_cache
from pprint import pprint
from re import search
from typing import Any

from beanie import init_beanie
import cv2
from cv2 import Mat
from dateparser import parse
import numpy as np
from numpy import array, dtype, ndarray
from PIL import Image, ImageEnhance
from pytesseract import image_to_string
from rapidocr_onnxruntime import RapidOCR

from api.db import get_db
from api.models.match import Match
from bot import get_project_root
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
        self.team_2_stats: dict[str, str] | None = None
        # img_recognition = ImageRecognition()
        # img_recognition.set_screenshot(cv2.imread(self.image_path) if self.image_path else self.image)
        # rois, champions = img_recognition.get_champions()
        # self.rois = rois
        # self.champions = champions

    @staticmethod
    def get_general_stats_rois(image):
        # Load the image
        image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # Show grayscale image for debugging
        # cv2.imshow("Grayscale Image", gray)
        # cv2.waitKey(0)

        # Apply binary thresholding (You might need to adjust the threshold value)
        _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)

        # Show threshold image for debugging
        # cv2.imshow("Threshold Image", thresh)
        # cv2.waitKey(0)

        # Find contours
        contours, hierarchy = cv2.findContours(thresh, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

        rois = []

        # Loop over contours
        for i, contour in enumerate(contours):
            x, y, w, h = cv2.boundingRect(contour)

            if 10 < h < 150 and 15 < w < 150 and 0.2 < w / h < 2.0:
                roi = [x - 15, y - 20, w + 30, h + 40]
                if rois:
                    if abs(rois[-1][0] - x) < 50:
                        rois[-1] = [x - 5, rois[-1][1], rois[-1][2] + w + 10, rois[-1][3]]
                        # Green for detected digits
                        cv2.rectangle(
                            image, (rois[-1][0], rois[-1][1]), (rois[-1][0] + w, rois[-1][1] + h), (0, 255, 0), 2
                        )
                    else:
                        # Store ROI coordinates
                        rois.append(roi)
                        # Green for detected digits
                        cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)
                else:
                    rois.append(roi)
                    cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)

        # Sort ROIs by their x-coordinate (from left to right)
        rois = sorted(rois, key=lambda b: b[0])

        # Display the image with detected ROIs
        # cv2.imshow("Digits with ROIs", image)
        # cv2.waitKey(0)
        # cv2.destroyAllWindows()
        rois = map(lambda _roi: (_roi[0] - 4, _roi[1] - 4, _roi[2] + 10, _roi[3] + 10), rois)

        return rois

    @staticmethod
    def preprocess_image(img) -> ndarray:
        # Convert to grayscale
        img = img.convert("L")

        # Increase contrast
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(0.1)

        # Resize if necessary (optional)
        img = img.resize((img.width * 2, img.height * 2))

        # Convert to NumPy array
        img_array = array(img)
        # cv_image = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
        # for roi in self.rois:
        #     x, y, w, h = roi
        #     cv2.rectangle(cv_image, (x, y), (x + w, y + h), (0, 255, 0), 2)
        # cv2.imshow("Detected ROIs", img_array)
        # cv2.waitKey(0)
        # cv2.destroyAllWindows()

        return img_array

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

        # cv2.imshow("Mask", img)
        # cv2.waitKey(0)
        # cv2.destroyAllWindows()

        # Convert the processed image back to PIL Image
        processed_img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))

        # Update the image attribute to the new processed image
        self.image = processed_img

    def change_team2_color_v2(self):
        # Load image using OpenCV for color processing
        img = self.image if not isinstance(self.image, str) else cv2.imread(self.image)

        # Convert image to HSV color space
        hsv_img = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

        # Define the color range for red in HSV
        lower_red1 = np.array([0, 50, 50])
        upper_red1 = np.array([10, 255, 255])
        lower_red2 = np.array([170, 50, 50])
        upper_red2 = np.array([180, 255, 255])

        # Create masks to isolate red regions
        mask1 = cv2.inRange(hsv_img, lower_red1, upper_red1)
        mask2 = cv2.inRange(hsv_img, lower_red2, upper_red2)
        mask = cv2.bitwise_or(mask1, mask2)

        # Convert the red areas to black text on white background
        result = cv2.bitwise_not(mask)

        # Convert result to 3-channel BGR for consistency
        result_bgr = cv2.cvtColor(result, cv2.COLOR_GRAY2BGR)

        # Apply a slight blur to reduce noise
        blurred_result = cv2.GaussianBlur(result_bgr, (3, 3), 0)

        # Convert to grayscale
        gray_result = cv2.cvtColor(blurred_result, cv2.COLOR_BGR2GRAY)

        # Increase contrast
        contrast_enhancer = ImageEnhance.Contrast(Image.fromarray(gray_result))
        contrasted_image = contrast_enhancer.enhance(2.0)  # Adjust the contrast as needed

        # Sharpen the image
        sharpen_enhancer = ImageEnhance.Sharpness(contrasted_image)
        sharpened_image = sharpen_enhancer.enhance(2.0)  # Adjust sharpness as needed

        # Convert back to NumPy array for OpenCV
        final_image_cv = np.array(sharpened_image)

        # Display the processed image for debugging
        # cv2.imshow("Enhanced Image for OCR", final_image_cv)
        # cv2.waitKey(0)
        # cv2.destroyAllWindows()
        # Configure Tesseract to use only digits and slashes
        custom_config = r"--psm 7 -c tessedit_char_whitelist=0123456789/ "
        result = image_to_string(final_image_cv, config=custom_config)
        find = search(r"(\d+)(?:/)(\d+)(?:/)(\d+)", result)
        try:
            self.team_2_stats = {
                "kills": find.group(1),
                "deaths": find.group(2),
                "assists": find.group(3),
            }
        except AttributeError:
            self.team_2_stats = {}

    def get_text(self) -> tuple[list[str], list[str], list[str]]:
        self.change_team2_color_v2()
        self.change_team2_color()
        # Get the dimensions of the image
        width, height = self.image.size

        # Crop the left part of the image (0% to 80% of the width)
        left = self.image.crop((0, 0, int(width * 0.75), height))

        right = self.image.crop((int(width * 0.8), int(0.3 * height), width, (int(height * 0.9))))

        right = right.resize((right.width * 3, right.height * 3))

        right_upper = right.crop((0, int(right.height * 0.3), right.width, int(right.height * 0.45)))
        right_lower = right.crop((0, int(right.height * 0.80), right.width, right.height))
        # Increase contrast
        # enhancer = ImageEnhance.Contrast(right_lower)
        # right_lower = enhancer.enhance(2)

        # Debugging: Display the cropped images
        # right_upper.show()
        # right_lower.show()

        right_upper_rois = self.get_general_stats_rois(right_upper)
        right_lower_rois = self.get_general_stats_rois(right_lower)

        numbers_images = {
            "blue": [],
            "red": [],
        }

        for roi in right_upper_rois:
            x, y, w, h = roi
            numbers_images["blue"].append(right_upper.crop((x, y, x + w, y + h)))

        for roi in right_lower_rois:
            x, y, w, h = roi
            # right_lower.crop((x, y, x + w, y + h)).show()
            numbers_images["red"].append(right_lower.crop((x, y, x + w, y + h)))

        results, elapse = get_engine()(self.preprocess_image(left))
        text_list_left = []
        for result in results:
            for text in result:
                if isinstance(text, str):
                    text_list_left.append(text)
        numbers_blue = []
        for number_image in numbers_images["blue"]:
            # Convert to grayscale
            grayscale_image = number_image.convert("L")

            # Optionally, increase contrast if needed
            contrast_enhancer = ImageEnhance.Contrast(grayscale_image)
            enhanced_image = contrast_enhancer.enhance(1.5)  # Adjust contrast factor slightly

            # Convert to NumPy array for OpenCV processing
            image_cv = np.array(enhanced_image)

            # Simple global thresholding
            _, thresholded_image = cv2.threshold(image_cv, 150, 255, cv2.THRESH_BINARY)

            # Optional: Sharpen the image using a kernel
            kernel_sharpening = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
            sharpened_image = cv2.filter2D(thresholded_image, -1, kernel_sharpening)
            # cv2.imshow("Cleaned Image", sharpened_image)
            # cv2.waitKey(0)
            # cv2.destroyAllWindows()
            result: str = image_to_string(sharpened_image, config="--psm 8 digits")
            numbers_blue.append(result.strip())

        numbers_red = []
        for number_image in numbers_images["red"]:
            result: str = image_to_string(number_image, config="--psm 8 digits")
            numbers_red.append(result.strip())

        # print(image_to_string(self.preprocess_image(left)))

        return text_list_left, numbers_blue, numbers_red

    def create_match(self, summoner_name: str) -> Match:
        summoner_name = remove_accents(summoner_name)
        text_list_left, numbers_blue, numbers_red = self.get_text()

        print(text_list_left)
        print(numbers_blue)
        print(numbers_red)

        fields = {}
        find_custom = text_list_left.index("Custom")
        # Find all indexes of 'BANS'
        # bans_objectives = [_index for _index, value in enumerate(text_list_left) if "BANS" in value]
        fields["duration"] = text_list_left[find_custom + 1]
        fields["date"] = parse(text_list_left[find_custom + 2])
        find_teams = [_index for _index, value in enumerate(text_list_left) if "TEA".lower() in value.lower()]
        for team in ["blue", "red"]:
            find_team = find_teams[0 if team == "blue" else 1]
            if not self.team_2_stats:
                self.team_2_stats = {
                    "kills": text_list_left[find_team + 1].split("/")[0],
                    "deaths": text_list_left[find_team + 1].split("/")[1],
                    "assists": text_list_left[find_team + 1].split("/")[2],
                }
            kills, deaths, assists = (
                text_list_left[find_team + 1].replace("X", "").strip().split("/")
                if team == "blue"
                else (self.team_2_stats["kills"], self.team_2_stats["deaths"], self.team_2_stats["assists"])
            )
            fields[f"{team}_team"] = {
                "stats": {
                    "kills": kills,
                    "deaths": deaths,
                    "assists": assists,
                    "total_gold": int(text_list_left[find_team + 2].replace(",", "")),
                },
            }
            fields[f"{team}_team"]["players"] = []
            sub_index = 0
            for index in range(0, 5):
                while True:
                    level = text_list_left[find_team + 3 + sub_index + (index * 5)]
                    try:
                        level = int(level)
                        if level == 1:
                            level = 11
                            break
                        elif 1 < level <= 18:
                            break
                        elif level > 18:
                            str_level = str(level)
                            level = int(str_level[0] + str_level[1])
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
                    name = text_list_left[find_team + 4 + sub_index + (index * 5)]
                    if not name.isupper():
                        if not name.isdigit():
                            break
                    sub_index += 1
                if "/" not in text_list_left[find_team + 5 + sub_index + (index * 5)]:
                    sub_index += 1
                player = {
                    "name": name,
                    "picked_champion": None,
                    "stats": {
                        "level": level,
                        "kills": int(text_list_left[find_team + 5 + sub_index + (index * 5)].split("/")[0]),
                        "deaths": int(text_list_left[find_team + 5 + sub_index + (index * 5)].split("/")[1]),
                        "assists": int(text_list_left[find_team + 5 + sub_index + (index * 5)].split("/")[2]),
                        "minions_killed": text_list_left[find_team + 6 + sub_index + (index * 5)],
                        "gold_earned": int(text_list_left[find_team + 7 + sub_index + (index * 5)].replace(",", "")),
                    },
                }
                fields[f"{team}_team"]["players"].append(player)
            text_list_right = numbers_blue if team == "blue" else numbers_red
            # bans_objectives = [_index for _index, value in enumerate(text_list_right) if "BANS" in value]
            towers_destroyed = int(text_list_right[0])
            inhibitors_destroyed = int(text_list_right[1])
            barons_slain = int(text_list_right[2])
            dragons_slain = int(text_list_right[3])
            rift_heralds_slain = int(text_list_right[4])
            void_grubs_slain = int(text_list_right[5])

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
        # for team in ["blue", "red"]:
        #     for player in fields[f"{team}_team"]["players"]:
        #         player["picked_champion"] = self.champions.pop(0)
        label_winning = "victory" if "victory".upper() in text_list_left else "defeat"
        if summoner_name in [player["name"] for player in fields["blue_team"]["players"]]:
            fields["winner"] = "blue" if label_winning == "victory" else "red"
        return Match(**fields)


if __name__ == "__main__":
    run(init_beanie(database=get_db(), document_models=[Match]))
    ocr = OCR(f"{get_project_root()}/tests/data/test10.png")
    match = ocr.create_match("PretinhoDaGuiné")
    pprint(match.model_dump())
