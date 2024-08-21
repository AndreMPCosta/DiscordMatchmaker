from numpy import array, ndarray
from PIL import Image, ImageEnhance
from rapidocr_onnxruntime import RapidOCR

from bot import get_project_root

engine = RapidOCR()


def preprocess_image(image_path: str) -> ndarray:
    img = Image.open(image_path)

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


def get_text(image_path: str) -> list[str]:
    results, elapse = engine(preprocess_image(image_path))
    text_list = []
    for result in results:
        for text in result:
            if isinstance(text, str):
                text_list.append(text)
    return text_list


if __name__ == "__main__":
    print(get_text(f"{get_project_root()}/tests/data/test13.png"))
