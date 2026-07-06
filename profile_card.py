from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageOps


CARD_WIDTH = 900
CARD_HEIGHT = 320
GREEN = (46, 204, 113)
DARK = (12, 14, 18)
DARK_2 = (20, 24, 31)
WHITE = (245, 245, 245)
GRAY = (150, 160, 170)


def _font(size: int, bold: bool = False):
    try:
        name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
        return ImageFont.truetype(name, size)
    except Exception:
        return ImageFont.load_default()


def create_profile_card(
    username: str,
    avatar_bytes: bytes,
    level: int,
    rank: int,
    total_xp: int,
    current_xp: int,
    needed_xp: int,
    role_name: str,
    server_name: str,
) -> BytesIO:
    card = Image.new("RGB", (CARD_WIDTH, CARD_HEIGHT), DARK)
    draw = ImageDraw.Draw(card)

    draw.rounded_rectangle((25, 25, CARD_WIDTH - 25, CARD_HEIGHT - 25), radius=28, fill=DARK_2)
    draw.rounded_rectangle((25, 25, CARD_WIDTH - 25, CARD_HEIGHT - 25), radius=28, outline=GREEN, width=3)

    avatar = Image.open(BytesIO(avatar_bytes)).convert("RGB").resize((150, 150))
    mask = Image.new("L", (150, 150), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.ellipse((0, 0, 150, 150), fill=255)

    avatar = ImageOps.fit(avatar, (150, 150))
    card.paste(avatar, (60, 75), mask)

    draw.ellipse((55, 70, 215, 230), outline=GREEN, width=5)

    username_font = _font(36, True)
    big_font = _font(28, True)
    normal_font = _font(22)
    small_font = _font(18)

    draw.text((250, 65), username[:22], font=username_font, fill=WHITE)
    draw.text((250, 115), f"Level {level}", font=big_font, fill=GREEN)
    draw.text((390, 119), f"Rank #{rank}", font=normal_font, fill=GRAY)

    draw.text((250, 160), f"Role: {role_name}", font=normal_font, fill=WHITE)
    draw.text((250, 195), f"XP: {current_xp:,} / {needed_xp:,}", font=normal_font, fill=WHITE)

    bar_x = 250
    bar_y = 235
    bar_w = 560
    bar_h = 28

    progress = 0 if needed_xp <= 0 else min(current_xp / needed_xp, 1)

    draw.rounded_rectangle((bar_x, bar_y, bar_x + bar_w, bar_y + bar_h), radius=14, fill=(45, 50, 60))
    draw.rounded_rectangle((bar_x, bar_y, bar_x + int(bar_w * progress), bar_y + bar_h), radius=14, fill=GREEN)

    draw.text((250, 275), f"Total XP: {total_xp:,}", font=small_font, fill=GRAY)
    draw.text((620, 275), server_name[:24], font=small_font, fill=GRAY)

    output = BytesIO()
    card.save(output, format="PNG")
    output.seek(0)
    return output
