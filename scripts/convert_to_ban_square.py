import os

from PIL import Image, ImageDraw

from bot import get_project_root


def create_ban_effect(image_path, output_path, line_color="gray", line_width=5):
    # Open the image file and ensure it has an alpha channel
    img = Image.open(image_path).convert("RGBA")

    # Get image size
    width, height = img.size

    # Create a new image to draw the diagonal lines
    overlay = Image.new("RGBA", img.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(overlay)

    # Draw one diagonal line to create the ban effect
    # draw.line([(0, 0), (width, height)], fill=line_color, width=line_width)
    draw.line([(0, height), (width, 0)], fill=line_color, width=line_width)

    # Combine the original image with the overlay containing the lines
    final_img = Image.alpha_composite(img, overlay)

    # Optionally, add a border around the image
    draw = ImageDraw.Draw(final_img)
    draw.rectangle([0, 0, width, height], outline=line_color, width=line_width)

    # Save the output image with transparency
    final_img.save(output_path, format="PNG")


def process_images(input_folder, output_folder, border_color="white", line_color="gray", line_width=5):
    # Create output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)

    for filename in os.listdir(input_folder):
        if filename.endswith(".png") or filename.endswith(".jpg"):
            input_path = os.path.join(input_folder, filename)
            output_path = os.path.join(output_folder, filename)

            create_ban_effect(input_path, output_path, line_color="gray", line_width=5)
            print(f"Processed {filename}")


# Example usage
_input_folder = f"{get_project_root()}/bot/ingestion/champions"
_output_folder = f"{get_project_root()}/bot/ingestion/champions_banned"

# Process images
process_images(_input_folder, _output_folder, border_color="#5c5b57", line_width=5)
