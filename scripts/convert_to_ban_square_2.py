import os

from PIL import Image, ImageDraw

from bot import get_project_root


def create_ban_effect(image_path, output_path, line_color="gray", line_width=5, shift_amount=5):
    # Open the image file and ensure it has an alpha channel
    img = Image.open(image_path).convert("RGBA")

    # Get image size
    width, height = img.size

    # Increase the canvas size based on the shift amount
    new_width = width + 2 * shift_amount
    new_height = height + 2 * shift_amount
    expanded_img = Image.new("RGBA", (new_width, new_height), (0, 0, 0, 0))

    # Center the original image in the expanded canvas
    expanded_img.paste(img, (shift_amount, shift_amount))

    # Create a new image to draw the diagonal lines and apply the shift effect
    overlay = Image.new("RGBA", expanded_img.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(overlay)

    # Draw one diagonal line to split the image into two triangles
    draw.line(
        [(shift_amount, new_height - shift_amount), (new_width - shift_amount, shift_amount)],
        fill=line_color,
        width=line_width,
    )

    # Shift the triangular borders
    upper_triangle = Image.new("RGBA", expanded_img.size, (255, 255, 255, 0))
    lower_triangle = Image.new("RGBA", expanded_img.size, (255, 255, 255, 0))

    # Draw the upper-left triangle
    draw_upper = ImageDraw.Draw(upper_triangle)
    draw_upper.polygon(
        [
            (shift_amount, new_height - shift_amount),
            (new_width - shift_amount, shift_amount),
            (shift_amount, shift_amount),
        ],
        fill=None,
        outline=line_color,
        width=line_width,
    )

    # Draw the lower-right triangle
    draw_lower = ImageDraw.Draw(lower_triangle)
    draw_lower.polygon(
        [
            (new_width - shift_amount, shift_amount),
            (new_width - shift_amount, new_height - shift_amount),
            (shift_amount, new_height - shift_amount),
        ],
        fill=None,
        outline=line_color,
        width=line_width,
    )

    # Create the final image by pasting the shifted triangles onto the expanded image
    final_img = expanded_img.copy()

    # Corrected shifts: Upper-left triangle moves left and up, lower-right triangle moves right and down
    final_img.paste(upper_triangle, (-shift_amount, -shift_amount), upper_triangle)
    final_img.paste(lower_triangle, (shift_amount, shift_amount), lower_triangle)

    # Save the output image with transparency
    final_img.save(output_path, format="PNG")


def process_images(input_folder, output_folder, line_color="gray", line_width=5, shift_amount=5):
    # Create output folder if it doesn't exist
    os.makedirs(output_folder, exist_ok=True)

    for filename in os.listdir(input_folder):
        if filename.endswith(".png") or filename.endswith(".jpg"):
            input_path = os.path.join(input_folder, filename)
            output_path = os.path.join(output_folder, filename)

            create_ban_effect(input_path, output_path, line_color, line_width, shift_amount)
            print(f"Processed {filename}")


# Example usage
_input_folder = f"{get_project_root()}/bot/ingestion/champions"
_output_folder = f"{get_project_root()}/bot/ingestion/champions_banned"

# Process images
process_images(_input_folder, _output_folder, line_color="#5c5b57", line_width=5, shift_amount=6)
