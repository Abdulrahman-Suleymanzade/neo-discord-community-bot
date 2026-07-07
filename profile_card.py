from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter


CARD_WIDTH = 1000
CARD_HEIGHT = 360

GREEN = (46, 204, 113)
GREEN_SOFT = (35, 180, 100)
DARK = (9, 11, 16)
PANEL = (18, 22, 30)
PANEL_2 = (28, 34, 45)
WHITE = (245, 247, 250)
GRAY = (160, 170, 180)
MUTED = (105, 115, 130)


def _font(size: int, bold: bool = False):
    try:
        name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
        return ImageFont.truetype(name, size)
    except Exception:
        return ImageFont.load_default()


def _center_text(draw, box, text, font, fill):
    bbox = draw.textbbox((0, 0), text, font=font)
    w = bbox[2] - bbox[0]
    h = bbox[3] - bbox[1]
    x1, y1, x2, y2 = box
    draw.text((x1 + (x2 - x1 - w) / 2, y1 + (y2 - y1 - h) / 2 - 1), text, font=font, fill=fill)


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
    card = Image.new("RGBA", (CARD_WIDTH, CARD_HEIGHT), DARK)

    glow = Image.new("RGBA", (CARD_WIDTH, CARD_HEIGHT), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.rounded_rectangle((45, 45, CARD_WIDTH - 45, CARD_HEIGHT - 45), radius=30, outline=GREEN, width=8)
    glow = glow.filter(ImageFilter.GaussianBlur(12))
    card = Image.alpha_composite(card, glow)

    draw = ImageDraw.Draw(card)

    draw.rounded_rectangle((55, 55, CARD_WIDTH - 55, CARD_HEIGHT - 55), radius=30, fill=PANEL)
    draw.rounded_rectangle((55, 55, CARD_WIDTH - 55, CARD_HEIGHT - 55), radius=30, outline=GREEN, width=4)

    title_font = _font(36, True)
    big_font = _font(30, True)
    normal_font = _font(22, True)
    small_font = _font(18)
    tiny_font = _font(15, True)

    avatar_size = 165
    avatar_x = 90
    avatar_y = 98

    avatar = Image.open(BytesIO(avatar_bytes)).convert("RGB")
    avatar = ImageOps.fit(avatar, (avatar_size, avatar_size))

    mask = Image.new("L", (avatar_size, avatar_size), 0)
    md = ImageDraw.Draw(mask)
    md.ellipse((0, 0, avatar_size, avatar_size), fill=255)

    card.paste(avatar, (avatar_x, avatar_y), mask)
    draw.ellipse(
        (avatar_x - 7, avatar_y - 7, avatar_x + avatar_size + 7, avatar_y + avatar_size + 7),
        outline=GREEN,
        width=6,
    )

    text_x = 310

    draw.text((text_x, 82), username[:22], font=title_font, fill=WHITE)
    draw.text((text_x, 124), server_name[:26], font=small_font, fill=GRAY)

    stat_y = 165
    stat_h = 62
    gap = 20
    box_w = 175

    boxes = [
        (text_x, stat_y, text_x + box_w, stat_y + stat_h, "LEVEL", str(level), GREEN),
        (text_x + box_w + gap, stat_y, text_x + box_w * 2 + gap, stat_y + stat_h, "RANK", f"#{rank}", WHITE),
        (text_x + (box_w + gap) * 2, stat_y, CARD_WIDTH - 85, stat_y + stat_h, "ROLE", role_name, WHITE),
    ]

    for x1, y1, x2, y2, label, value, color in boxes:
        draw.rounded_rectangle((x1, y1, x2, y2), radius=18, fill=PANEL_2)
        draw.text((x1 + 18, y1 + 12), label, font=tiny_font, fill=MUTED)
        draw.text((x1 + 18, y1 + 31), value[:20], font=normal_font, fill=color)

    bar_x = text_x
    bar_y = 267
    bar_w = CARD_WIDTH - text_x - 85
    bar_h = 28

    progress = 0 if needed_xp <= 0 else max(0, min(current_xp / needed_xp, 1))
    fill_w = int(bar_w * progress)

    draw.text((bar_x, 240), "XP Progress", font=small_font, fill=GRAY)
    draw.text((CARD_WIDTH - 285, 240), f"{current_xp:,} / {needed_xp:,} XP", font=small_font, fill=GRAY)

    draw.rounded_rectangle((bar_x, bar_y, bar_x + bar_w, bar_y + bar_h), radius=14, fill=(48, 55, 70))
    if fill_w > 0:
        draw.rounded_rectangle((bar_x, bar_y, bar_x + fill_w, bar_y + bar_h), radius=14, fill=GREEN_SOFT)

    draw.text((bar_x, 312), f"Total XP: {total_xp:,}", font=small_font, fill=GRAY)

    output = BytesIO()
    card.convert("RGB").save(output, format="PNG")
    output.seek(0)
    return output
