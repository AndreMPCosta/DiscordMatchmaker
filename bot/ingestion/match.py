from dataclasses import dataclass, field
from os import listdir
from typing import Any

import cv2
from cv2 import Mat
import numpy as np

from bot import get_project_root


@dataclass
class ImageRecognition:
    champion_images: dict[str, np.ndarray] = field(default_factory=dict)
    adjustments: dict[int, tuple[int, int, int, int]] = field(default_factory=dict)
    screenshot: Mat | np.ndarray[Any, np.dtype] = None

    def __post_init__(self):
        for _image in listdir(f"{get_project_root()}/bot/ingestion/champions"):
            self.champion_images[_image.split(".")[0]] = cv2.imread(
                f"{get_project_root()}/bot/ingestion/champions/{_image}"
            )
        self.adjustments = {
            1: (-1, 1, 0, -2),
            9: (-1, 2, 2, -1),
        }

    def set_screenshot(self, screenshot: Mat | np.ndarray[Any, np.dtype]) -> None:
        self.screenshot = screenshot

    # Function to match template and return champion name
    @staticmethod
    def match_champion(image: Mat | np.ndarray[Any, np.dtype], template_dict):
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
                best_match = champ

        return best_match

    def get_raw_champions(self, rois: list[tuple[int, int, int, int]]) -> list[str]:
        # Iterate over each ROI to identify champions
        identified_champions = []

        for roi in rois:
            x, y, w, h = roi
            roi_image = self.screenshot[y : y + h, x : x + w]
            champion = self.match_champion(roi_image, self.champion_images)
            identified_champions.append(champion)
        return identified_champions

    def calculate_rois(self, indexes: list[int] | None = None) -> list[tuple[int, int, int, int]]:
        # Define the region on the left side where the portraits are located
        height, width = self.screenshot.shape[:2]
        left_side = self.screenshot[0:height, 0 : int(width * 0.3)]  # Adjust the width percentage as needed

        # Convert the cropped left side of the image from BGR to HSV color space
        hsv_image = cv2.cvtColor(left_side, cv2.COLOR_BGR2HSV)

        # Define the hex color codes for the borders
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

            if 0.5 < aspect_ratio < 2.0 and 30 < w < 200 and 30 < h < 200:
                filtered_contours.append(contour)
        for i, contour in enumerate(filtered_contours, 1):
            x, y, w, h = cv2.boundingRect(contour)
            if indexes is not None and i in indexes:
                x = x + self.adjustments.get(i)[0]
                w = w + self.adjustments.get(i)[1]
                h = h + self.adjustments.get(i)[2]
                y = y + self.adjustments.get(i)[3]
            cv2.rectangle(left_side, (x, y), (x + w, y + h), (0, 255, 0), 2)
            final_rois.append((x, y, w, h))

        # Show the detected ROIs in the cropped left side
        # cv2.imshow("Detected ROIs on Left Side", left_side)
        # cv2.waitKey(0)
        # cv2.destroyAllWindows()
        final_rois.reverse()
        return final_rois

    def get_champions(self) -> list[str]:
        rois = self.calculate_rois(indexes=[1, 9])
        return self.get_raw_champions(rois)


if __name__ == "__main__":
    img_recognition = ImageRecognition()
    img_recognition.set_screenshot(cv2.imread(f"{get_project_root()}/bot/ingestion/test3.png"))
    print(img_recognition.get_champions())