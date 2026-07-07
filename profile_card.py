from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter

CARD_WIDTH = 1400
CARD_HEIGHT = 800

GREEN = (46, 204, 113)
DARK = (5, 9, 14)
PANEL = (13, 18, 26)
PANEL_2 = (18, 25, 36)
WHITE = (245, 248, 252)
GRAY = (160, 170, 185)
MUTED = (95, 105, 120)


ROLE_COLORS = {
    "Bronze": (205, 127, 50),
    "Silver": (190, 195, 205),
    "Gold": (255, 200, 55),
    "Platinum": (70, 160, 255),
    "Diamond": (145, 90, 255),
    "Legend": (255, 220, 70),
}


def _font(size: int, bold: bool = False):
    try:
        name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
        return ImageFont.truetype(name, size)
    except Exception:
        return ImageFont.load_default()


def _clean_role(role_name: str):
    for name in ROLE_COLORS:
        if name.lower() in role_name.lower():
            return name
    return "No Role"


def _draw_role_icon(draw, x, y, role):
    color = ROLE_COLORS.get(role, GRAY)
    draw.ellipse((x, y, x + 42, y + 42), fill=color)
    draw.ellipse((x + 9, y + 9, x + 33, y + 33), fill=PANEL_2)
    draw.text((x + 14, y + 8), "★", font=_font(22, True), fill=color)


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
    role_clean = _clean_role(role_name)

    card = Image.new("RGBA", (CARD_WIDTH, CARD_HEIGHT), DARK)

    glow = Image.new("RGBA", (CARD_WIDTH, CARD_HEIGHT), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.rounded_rectangle((55, 55, CARD_WIDTH - 55, CARD_HEIGHT - 55), radius=46, outline=GREEN, width=12)
    glow = glow.filter(ImageFilter.GaussianBlur(18))
    card = Image.alpha_composite(card, glow)

    draw = ImageDraw.Draw(card)

    draw.rounded_rectangle((65, 65, CARD_WIDTH - 65, CARD_HEIGHT - 65), radius=46, fill=PANEL)
    draw.rounded_rectangle((65, 65, CARD_WIDTH - 65, CARD_HEIGHT - 65), radius=46, outline=GREEN, width=5)

    title_font = _font(54, True)
    subtitle_font = _font(28)
    label_font = _font(25, True)
    value_font = _font(48, True)
    normal_font = _font(31, True)
    small_font = _font(24)
    tiny_font = _font(21)

    avatar_size = 270
    avatar_x = 105
    avatar_y = 145

    avatar = Image.open(BytesIO(avatar_bytes)).convert("RGB")
    avatar = ImageOps.fit(avatar, (avatar_size, avatar_size))

    mask = Image.new("L", (avatar_size, avatar_size), 0)
    md = ImageDraw.Draw(mask)
    md.ellipse((0, 0, avatar_size, avatar_size), fill=255)

    avatar_glow = Image.new("RGBA", (CARD_WIDTH, CARD_HEIGHT), (0, 0, 0, 0))
    ag = ImageDraw.Draw(avatar_glow)
    ag.ellipse((avatar_x - 12, avatar_y - 12, avatar_x + avatar_size + 12, avatar_y + avatar_size + 12), fill=(46, 204, 113, 130))
    avatar_glow = avatar_glow.filter(ImageFilter.GaussianBlur(18))
    card = Image.alpha_composite(card, avatar_glow)
    draw = ImageDraw.Draw(card)

    card.paste(avatar, (avatar_x, avatar_y), mask)
    draw.ellipse((avatar_x - 10, avatar_y - 10, avatar_x + avatar_size + 10, avatar_y + avatar_size + 10), outline=GREEN, width=8)

    text_x = 455

    draw.text((text_x, 120), username[:22], font=title_font, fill=WHITE)
    draw.ellipse((text_x, 205, text_x + 18, 205 + 18), fill=GREEN)
    draw.text((text_x + 32, 195), server_name[:30], font=subtitle_font, fill=GRAY)

    box_y = 270
    box_h = 135
    gap = 30
    box_w = 255

    boxes = [
        (text_x, box_y, text_x + box_w, box_y + box_h, "LEVEL", str(level), GREEN),
        (text_x + box_w + gap, box_y, text_x + box_w * 2 + gap, box_y + box_h, "RANK", f"#{rank}", WHITE),
        (text_x + (box_w + gap) * 2, box_y, CARD_WIDTH - 110, box_y + box_h, "ROLE", role_clean, WHITE),
    ]

    for x1, y1, x2, y2, label, value, color in boxes:
        draw.rounded_rectangle((x1, y1, x2, y2), radius=24, fill=PANEL_2, outline=(45, 55, 70), width=2)
        draw.text((x1 + 32, y1 + 28), label, font=label_font, fill=MUTED)

        if label == "ROLE":
            _draw_role_icon(draw, x1 + 32, y1 + 73, role_clean)
            draw.text((x1 + 88, y1 + 72), value, font=normal_font, fill=color)
        else:
            draw.text((x1 + 32, y1 + 68), value, font=value_font, fill=color)

    roles_y = 440
    roles_x = text_x
    roles_w = CARD_WIDTH - text_x - 110
    roles_h = 115

    draw.rounded_rectangle((roles_x, roles_y, roles_x + roles_w, roles_y + roles_h), radius=24, fill=(10, 15, 22), outline=(40, 50, 65), width=2)

    role_names = ["Bronze", "Silver", "Gold", "Platinum", "Diamond", "Legend"]
    step = roles_w // 6

    for i, name in enumerate(role_names):
        cx = roles_x + step * i + step // 2 - 20
        _draw_role_icon(draw, cx, roles_y + 22, name)
        color = ROLE_COLORS[name] if name == role_clean else GRAY
        draw.text((roles_x + step * i + 32, roles_y + 73), name, font=tiny_font, fill=color)

    total_box_x = 105
    total_box_y = 505
    total_box_w = 270
    total_box_h = 170

    draw.rounded_rectangle((total_box_x, total_box_y, total_box_x + total_box_w, total_box_y + total_box_h), radius=28, fill=(10, 15, 22), outline=(45, 55, 70), width=2)
    draw.text((total_box_x + 38, total_box_y + 38), "TOTAL XP", font=label_font, fill=GRAY)
    draw.text((total_box_x + 38, total_box_y + 88), f"{total_xp:,}", font=value_font, fill=GREEN)

    bar_x = text_x
    bar_y = 610
    bar_w = CARD_WIDTH - text_x - 110
    bar_h = 55

    progress = 0 if needed_xp <= 0 else max(0, min(current_xp / needed_xp, 1))
    fill_w = int(bar_w * progress)

    draw.text((bar_x, 570), "XP PROGRESS", font=label_font, fill=GRAY)
    draw.text((CARD_WIDTH - 390, 570), f"{current_xp:,} / {needed_xp:,} XP", font=label_font, fill=WHITE)

    draw.rounded_rectangle((bar_x, bar_y, bar_x + bar_w, bar_y + bar_h), radius=28, fill=(35, 42, 55), outline=(55, 65, 80), width=2)

    if fill_w > 0:
        draw.rounded_rectangle((bar_x, bar_y, bar_x + fill_w, bar_y + bar_h), radius=28, fill=GREEN)

    percent = int(progress * 100)
    draw.text((bar_x, 690), f"{percent}% to next level", font=small_font, fill=GRAY)
    draw.text((CARD_WIDTH - 280, 690), "Keep going!", font=small_font, fill=GREEN)

    output = BytesIO()
    card.convert("RGB").save(output, format="PNG")
    output.seek(0)
    return output
