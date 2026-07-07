from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter


CARD_WIDTH = 1000
CARD_HEIGHT = 360

GREEN = (46, 204, 113)
GREEN_DARK = (22, 140, 78)
DARK = (8, 10, 14)
PANEL = (17, 21, 29)
PANEL_2 = (24, 29, 39)
WHITE = (245, 247, 250)
GRAY = (155, 165, 175)
MUTED = (95, 105, 118)


def _font(size: int, bold: bool = False):
    try:
        name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
        return ImageFont.truetype(name, size)
    except Exception:
        return ImageFont.load_default()


def _rounded_avatar(avatar_bytes: bytes, size: int):
    avatar = Image.open(BytesIO(avatar_bytes)).convert("RGB")
    avatar = ImageOps.fit(avatar, (size, size))

    mask = Image.new("L", (size, size), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.ellipse((0, 0, size, size), fill=255)

    return avatar, mask


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

    glow = Image.new("RGBA", (CARD_WIDTH, CARD_HEIGHT), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    glow_draw.rounded_rectangle((35, 35, CARD_WIDTH - 35, CARD_HEIGHT - 35), radius=34, outline=GREEN, width=8)
    glow = glow.filter(ImageFilter.GaussianBlur(10))
    card = Image.alpha_composite(card.convert("RGBA"), glow)

    draw = ImageDraw.Draw(card)

    draw.rounded_rectangle((40, 40, CARD_WIDTH - 40, CARD_HEIGHT - 40), radius=34, fill=PANEL)
    draw.rounded_rectangle((40, 40, CARD_WIDTH - 40, CARD_HEIGHT - 40), radius=34, outline=GREEN, width=3)

    for i in range(0, CARD_WIDTH, 40):
        draw.line((i, 40, i - 140, CARD_HEIGHT - 40), fill=(12, 16, 22), width=1)

    avatar_size = 170
    avatar_x = 75
    avatar_y = 95

    avatar, mask = _rounded_avatar(avatar_bytes, avatar_size)
    card.paste(avatar, (avatar_x, avatar_y), mask)

    draw.ellipse(
        (avatar_x - 7, avatar_y - 7, avatar_x + avatar_size + 7, avatar_y + avatar_size + 7),
        outline=GREEN,
        width=6,
    )

    username_font = _font(34, True)
    label_font = _font(18, True)
    normal_font = _font(22)
    big_font = _font(30, True)
    small_font = _font(17)

    text_x = 285

    draw.text((text_x, 72), username[:24], font=username_font, fill=WHITE)
    draw.text((text_x, 118), server_name[:28], font=small_font, fill=GRAY)

    draw.rounded_rectangle((text_x, 155, text_x + 150, 205), radius=18, fill=PANEL_2)
    draw.text((text_x + 18, 166), "LEVEL", font=label_font, fill=MUTED)
    draw.text((text_x + 92, 160), str(level), font=big_font, fill=GREEN)

    draw.rounded_rectangle((text_x + 175, 155, text_x + 330, 205), radius=18, fill=PANEL_2)
    draw.text((text_x + 193, 166), "RANK", font=label_font, fill=MUTED)
    draw.text((text_x + 265, 160), f"#{rank}", font=big_font, fill=WHITE)

    draw.rounded_rectangle((text_x + 355, 155, CARD_WIDTH - 75, 205), radius=18, fill=PANEL_2)
    draw.text((text_x + 375, 166), "ROLE", font=label_font, fill=MUTED)
    draw.text((text_x + 440, 162), role_name[:22], font=normal_font, fill=WHITE)

    draw.text((text_x, 230), f"XP Progress", font=label_font, fill=GRAY)
    draw.text((CARD_WIDTH - 265, 228), f"{current_xp:,} / {needed_xp:,} XP", font=small_font, fill=GRAY)

    bar_x = text_x
    bar_y = 262
    bar_w = CARD_WIDTH - text_x - 75
    bar_h = 30

    progress = 0 if needed_xp <= 0 else max(0, min(current_xp / needed_xp, 1))
    fill_w = max(12, int(bar_w * progress)) if progress > 0 else 0

    draw.rounded_rectangle((bar_x, bar_y, bar_x + bar_w, bar_y + bar_h), radius=15, fill=(45, 51, 64))
    if fill_w > 0:
        draw.rounded_rectangle((bar_x, bar_y, bar_x + fill_w, bar_y + bar_h), radius=15, fill=GREEN)

    draw.text((text_x, 310), f"Total XP: {total_xp:,}", font=small_font, fill=GRAY)
    draw.text((CARD_WIDTH - 230, 310), "Neo Profile", font=small_font, fill=GREEN_DARK)

    output = BytesIO()
    card.convert("RGB").save(output, format="PNG")
    output.seek(0)
    return output
