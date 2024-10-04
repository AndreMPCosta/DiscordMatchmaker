from dataclasses import dataclass, field
from os import listdir
from typing import Any, Literal

import cv2
from cv2 import Mat
import numpy as np

from api.consts import Champion
from bot import get_project_root

generic_adjustments = {
    1: [(-1, 1, 0, -2)],
    5: [(0, 1, 0, -1)],
    9: [(0, 1, 1, 0)],
}


@dataclass
class ImageRecognition:
    original_champions_images: dict[str, np.ndarray] = field(default_factory=dict)
    champion_images: dict[str, np.ndarray] = field(default_factory=dict)
    ban_images: dict[str, np.ndarray] = field(default_factory=dict)
    adjustments: dict[int, tuple[int, int, int, int]] = field(default_factory=dict)
    screenshot: Mat | np.ndarray[Any, np.dtype] = None
    debug: bool = False

    def __post_init__(self):
        for _image in listdir(f"{get_project_root()}/bot/ingestion/champions"):
            self.original_champions_images[_image.split(".")[0]] = cv2.imread(
                f"{get_project_root()}/bot/ingestion/champions/{_image}"
            )

        for _image in listdir(f"{get_project_root()}/bot/ingestion/champions2"):
            self.champion_images[_image.split(".")[0]] = cv2.imread(
                f"{get_project_root()}/bot/ingestion/champions2/{_image}"
            )

        self.adjustments = {
            1: (-2, 2, 2, 0),  # (-1, 1, 0, -2)
            9: (-1, 2, 2, -1),  # (-1, 2, 2, -1)
        }

    def set_screenshot(self, screenshot: Mat | np.ndarray[Any, np.dtype]) -> None:
        self.screenshot = screenshot

    # Function to match template and return champion name
    @staticmethod
    def match_champion(image: Mat | np.ndarray[Any, np.dtype], template_dict) -> Champion | None:
        best_match = None
        highest_val = 0
        # Resize the image if needed
        for champ, template in template_dict.items():
            _template = cv2.resize(template, (image.shape[1], image.shape[0]))

            # Normalize the images to minimize lighting differences
            image_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            template_gray = cv2.cvtColor(_template, cv2.COLOR_BGR2GRAY)

            res = cv2.matchTemplate(image_gray, template_gray, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)

            if max_val > highest_val:
                highest_val = max_val
                best_match: Champion | None = champ

        return best_match

    def get_raw_champions(
        self, rois: list[tuple[int, int, int, int]], images: dict[str, np.ndarray]
    ) -> list[Champion | None]:
        # Iterate over each ROI to identify champions
        identified_champions = []

        for index, roi in enumerate(rois):
            x, y, w, h = roi
            roi_image = self.screenshot[y : y + h, x : x + w]
            champion = self.match_champion(roi_image, images)
            if champion == "MonkeyKing":
                champion = "Wukong"
            increment = 1
            while champion is None:
                roi_image = self.screenshot[y : y + h + increment, x : x + w + increment]
                if self.debug:
                    height, width = self.screenshot.shape[:2]
                    crop = self.screenshot[0:height, 0 : int(width * 0.2)]
                    cv2.rectangle(crop, (x, y), (x + w + increment, y + h + increment), (255, 255, 0), 2)
                    cv2.imshow("Detected ROIs", crop)
                    cv2.waitKey(0)
                    cv2.destroyAllWindows()
                champion: Champion | None = self.match_champion(roi_image, self.champion_images)
                if champion:
                    break
                increment += 1
            identified_champions.append(champion)
        return identified_champions

    def calculate_rois(
        self, side: Literal["left", "right"] = "left", factor: float = 0.2, hex_colors: list[str] = None
    ) -> list[tuple[int, int, int, int]]:
        # Define the region on the left side where the portraits are located
        height, width = self.screenshot.shape[:2]

        if side == "left":
            crop = self.screenshot[0:height, 0 : int(width * factor)]
        else:
            crop = self.screenshot[0:height, int(width * (1 - factor)) : width]

        # Convert the cropped left side of the image from BGR to HSV color space
        hsv_image = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)

        if hex_colors is None:
            hex_colors = ["#eec133", "#846f36", "#8c7332", "#deb533"]

        # Convert hex to HSV
        bgr_colors = [tuple(int(hex_color.lstrip("#")[i : i + 2], 16) for i in (4, 2, 0)) for hex_color in hex_colors]
        hsv_colors = [cv2.cvtColor(np.uint8([[bgr_color]]), cv2.COLOR_BGR2HSV)[0][0] for bgr_color in bgr_colors]

        # Create masks for each color with a broader range
        masks = []
        for hsv_color in hsv_colors:
            hsv_color_int32 = hsv_color.astype(np.int32)

            lower_bound = np.array(
                [hsv_color_int32[0] - 15, hsv_color_int32[1] - 70, hsv_color_int32[2] - 70], dtype=np.int32
            )
            upper_bound = np.array(
                [hsv_color_int32[0] + 15, hsv_color_int32[1] + 70, hsv_color_int32[2] + 70], dtype=np.int32
            )

            lower_bound = np.clip(lower_bound, 0, 255).astype(np.uint8)
            upper_bound = np.clip(upper_bound, 0, 255).astype(np.uint8)

            mask = cv2.inRange(hsv_image, lower_bound, upper_bound)
            masks.append(mask)

        # Combine all masks (using bitwise OR)
        combined_mask = masks[0]
        for mask in masks[1:]:
            combined_mask = cv2.bitwise_or(combined_mask, mask)

        # Display the combined mask for debugging
        # cv2.imshow("Combined Mask (HSV)", combined_mask)
        # cv2.waitKey(0)

        # Find contours in the combined mask
        contours, _ = cv2.findContours(combined_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        final_rois = []
        filtered_contours = []
        # Filter and draw contours based on a broader range for size and aspect ratio
        for i, contour in enumerate(contours[:-2], 1):
            x, y, w, h = cv2.boundingRect(contour)
            aspect_ratio = w / float(h)

            if 0.9 < aspect_ratio < 1.1 and 30 < w < 200 and 30 < h < 200:
                filtered_contours.append(contour)
        converted_contours = [cv2.boundingRect(contour) for contour in filtered_contours]
        max_width, max_height = (
            max(converted_contours, key=lambda element: element[2])[2],
            max(converted_contours, key=lambda element: element[3])[3],
        )
        # print(converted_contours)
        # print(max_width, max_height)

        for contour in converted_contours:
            x, y, w, h = contour
            if w + 5 < max_width or h + 5 < max_height:
                continue
            cv2.rectangle(crop, (x, y), (x + w, y + h), (0, 255, 0), 2)
            final_rois.append((x, y, w, h))
        if self.debug:
            print(final_rois)

        # Show the detected ROIs in the cropped left side
        if self.debug:
            cv2.imshow("Detected ROIs", crop)
            cv2.waitKey(0)
            cv2.destroyAllWindows()
        final_rois.reverse()
        return final_rois

    def get_champions(self) -> list[Champion | None]:
        _rois = self.calculate_rois()
        return self.get_raw_champions(_rois, self.champion_images)


if __name__ == "__main__":
    img_recognition = ImageRecognition(debug=True)
    img_recognition.set_screenshot(cv2.imread(f"{get_project_root()}/tests/data/test16.png"))
    champions = img_recognition.get_champions()
    print(champions)
    # print(img_recognition.calculate_rois("right", 0.7, ["#5c5b57"]))
    # print(img_recognition.get_raw_champions(img_recognition.calculate_rois("right", 0.2, ["#5c5b57"]),
    #                                         img_recognition.ban_images))
