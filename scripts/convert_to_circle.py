import os

from PIL import Image, ImageDraw

from bot import get_project_root


def create_circular_image(image_path, output_path, crop_factor=0.8, border_colors=None, border_width=10):
    # Open the image file and ensure it has an alpha channel
    img = Image.open(image_path).convert("RGBA")

    # Calculate the size of the circle (based on crop_factor)
    size = img.size
    circle_radius = int(min(size) * crop_factor / 2)
    center = (size[0] // 2, size[1] // 2)

    # Create a mask for the circle
    mask = Image.new("L", size, 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.ellipse(
        (center[0] - circle_radius, center[1] - circle_radius, center[0] + circle_radius, center[1] + circle_radius),
        fill=255,
    )

    # Create a new image for the border with a transparent background
    bordered_img = Image.new("RGBA", size, (255, 255, 255, 0))

    # Draw the borders using the specified colors
    if border_colors:
        for i, color in enumerate(border_colors):
            current_radius = circle_radius + border_width * (len(border_colors) - i)
            draw = ImageDraw.Draw(bordered_img)
            draw.ellipse(
                (
                    center[0] - current_radius,
                    center[1] - current_radius,
                    center[0] + current_radius,
                    center[1] + current_radius,
                ),
                fill=color,
            )

    # Apply the circular mask to the original image
    circular_img = Image.new("RGBA", size)
    circular_img = Image.composite(img, bordered_img, mask)

    # Combine the circular image with the border
    final_img = Image.alpha_composite(bordered_img, circular_img)

    # Save the output image with transparency
    final_img.save(output_path, format="PNG")


def process_images(input_folder, output_folder, crop_factor=0.8, border_colors=None, border_width=10):
    # Create output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)

    for filename in os.listdir(input_folder):
        if filename.endswith(".png") or filename.endswith(".jpg"):
            input_path = os.path.join(input_folder, filename)
            output_path = os.path.join(output_folder, filename)

            create_circular_image(
                input_path, output_path, crop_factor=crop_factor, border_colors=border_colors, border_width=border_width
            )
            print(f"Processed {filename}")


# Define the hex color codes for the borders
_border_colors = ["#eec133", "#846f36", "#8c7332", "#deb533"]

# Example usage
_input_folder = f"{get_project_root()}/bot/ingestion/champions"
_output_folder = f"{get_project_root()}/bot/ingestion/champions2"

# Adjust crop_factor and border_width as needed
process_images(_input_folder, _output_folder, crop_factor=0.85, border_colors=_border_colors, border_width=1)
