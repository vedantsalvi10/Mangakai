import sys, json
from PIL import Image, ImageDraw, ImageFont
import textwrap

def draw_text_bubble(image_path, output_path, bubble_data):
    img = Image.open(image_path).convert("RGB")
    draw = ImageDraw.Draw(img)
    width, height = img.size

    # Bubble height
    bubble_height = int(height * 0.15)
    bubble_box = [0, height - bubble_height, width, height]
    draw.rectangle(bubble_box, fill="white", outline="black", width=4)

    # Font sizes
    font_size = 15
    try:
        font_regular = ImageFont.truetype("fonts/animeace2_reg.otf", font_size)
        font_bold = ImageFont.truetype("fonts/animeace2_bld.otf", font_size)  # Bold variant
    except:
        font_regular = ImageFont.load_default()
        font_bold = ImageFont.load_default()

    x, y = 20, height - bubble_height + 20
    line_spacing = font_size + 8

    for bubble in bubble_data:
        if bubble["type"] == "narration":
            wrapped_lines = textwrap.wrap(bubble["text"], width=40)
            for line in wrapped_lines:
                draw.text((x, y), line, font=font_regular, fill="black")
                y += line_spacing

        elif bubble["type"] == "dialogue":
            speaker = f"{bubble['speaker']}: "
            message = bubble['text']

            # Measure speaker text to know where message should start
            speaker_width = draw.textlength(speaker, font=font_bold)

            # Wrap message to fit remaining width
            max_width = width - x - 20
            wrapped_message = textwrap.wrap(message, width=40)

            for i, line in enumerate(wrapped_message):
                if i == 0:
                    draw.text((x, y), speaker, font=font_bold, fill="black")
                    draw.text((x + speaker_width, y), line, font=font_regular, fill="black")
                else:
                    draw.text((x, y), line, font=font_regular, fill="black")
                y += line_spacing
        else:
            # Fallback (just print raw text)
            draw.text((x, y), bubble["text"], font=font_regular, fill="black")
            y += line_spacing

    img.save(output_path)
    print(f"✅ Bubble added at: {output_path}")

if __name__ == "__main__":
    image_path = sys.argv[1]
    output_path = sys.argv[2]
    bubble_json = sys.argv[3]
    bubble_data = json.loads(bubble_json)
    draw_text_bubble(image_path, output_path, bubble_data)
