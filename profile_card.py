from io import BytesIO
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter

CARD_WIDTH = 1100
CARD_HEIGHT = 420

GREEN = (46, 204, 113)
GREEN_DARK = (26, 170, 92)
BG = (7, 10, 16)
PANEL = (17, 22, 31)
BOX = (25, 31, 43)
BAR_BG = (55, 62, 78)
WHITE = (245, 247, 250)
GRAY = (170, 178, 190)
MUTED = (105, 115, 130)

ROLE_NAMES = ["Bronze", "Silver", "Gold", "Platinum", "Diamond", "Legend"]


def _font(size: int, bold: bool = False):
    try:
        name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
        return ImageFont.truetype(name, size)
    except Exception:
        return ImageFont.load_default()


def _clean_role(role_name: str) -> str:
    for role in ROLE_NAMES:
        if role.lower() in role_name.lower():
            return role
    return "No Role"


def _role_badge(role: str) -> str:
    badges = {
        "Bronze": "BRONZE",
        "Silver": "SILVER",
        "Gold": "GOLD",
        "Platinum": "PLATINUM",
        "Diamond": "DIAMOND",
        "Legend": "LEGEND",
    }
    return badges.get(role, "NO ROLE")


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

    card = Image.new("RGBA", (CARD_WIDTH, CARD_HEIGHT), BG)

    glow = Image.new("RGBA", (CARD_WIDTH, CARD_HEIGHT), (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.rounded_rectangle((35, 35, CARD_WIDTH - 35, CARD_HEIGHT - 35), radius=34, outline=GREEN, width=8)
    glow = glow.filter(ImageFilter.GaussianBlur(10))
    card = Image.alpha_composite(card, glow)

    draw = ImageDraw.Draw(card)
    draw.rounded_rectangle((45, 45, CARD_WIDTH - 45, CARD_HEIGHT - 45), radius=34, fill=PANEL)
    draw.rounded_rectangle((45, 45, CARD_WIDTH - 45, CARD_HEIGHT - 45), radius=34, outline=GREEN, width=4)

    title_font = _font(42, True)
    subtitle_font = _font(22)
    label_font = _font(17, True)
    value_font = _font(28, True)
    small_font = _font(19)
    xp_font = _font(22, True)

    avatar_size = 190
    avatar_x = 85
    avatar_y = 105

    avatar = Image.open(BytesIO(avatar_bytes)).convert("RGB")
    avatar = ImageOps.fit(avatar, (avatar_size, avatar_size))

    mask = Image.new("L", (avatar_size, avatar_size), 0)
    md = ImageDraw.Draw(mask)
    md.ellipse((0, 0, avatar_size, avatar_size), fill=255)

    avatar_glow = Image.new("RGBA", (CARD_WIDTH, CARD_HEIGHT), (0, 0, 0, 0))
    ag = ImageDraw.Draw(avatar_glow)
    ag.ellipse((avatar_x - 12, avatar_y - 12, avatar_x + avatar_size + 12, avatar_y + avatar_size + 12), fill=(46, 204, 113, 110))
    avatar_glow = avatar_glow.filter(ImageFilter.GaussianBlur(13))
    card = Image.alpha_composite(card, avatar_glow)
    draw = ImageDraw.Draw(card)

    card.paste(avatar, (avatar_x, avatar_y), mask)
    draw.ellipse((avatar_x - 7, avatar_y - 7, avatar_x + avatar_size + 7, avatar_y + avatar_size + 7), outline=GREEN, width=6)

    x = 330

    draw.text((x, 82), username[:22], font=title_font, fill=WHITE)
    draw.ellipse((x, 143, x + 13, 156), fill=GREEN)
    draw.text((x + 24, 136), server_name[:30], font=subtitle_font, fill=GRAY)

    box_y = 185
    box_h = 78
    gap = 18

    boxes = [
        (x, box_y, x + 170, box_y + box_h, "LEVEL", str(level), GREEN),
        (x + 188, box_y, x + 358, box_y + box_h, "RANK", f"#{rank}", WHITE),
        (x + 376, box_y, CARD_WIDTH - 80, box_y + box_h, "ROLE", _role_badge(role_clean), WHITE),
    ]

    for x1, y1, x2, y2, label, value, color in boxes:
        draw.rounded_rectangle((x1, y1, x2, y2), radius=18, fill=BOX)
        draw.text((x1 + 20, y1 + 13), label, font=label_font, fill=MUTED)
        draw.text((x1 + 20, y1 + 39), value, font=value_font, fill=color)

    bar_x = x
    bar_y = 315
    bar_w = CARD_WIDTH - x - 80
    bar_h = 32

    progress = 0 if needed_xp <= 0 else max(0, min(current_xp / needed_xp, 1))
    fill_w = int(bar_w * progress)

    draw.text((bar_x, 282), "XP PROGRESS", font=label_font, fill=GRAY)
    draw.text((CARD_WIDTH - 250, 278), f"{current_xp:,} / {needed_xp:,} XP", font=xp_font, fill=WHITE)

    draw.rounded_rectangle((bar_x, bar_y, bar_x + bar_w, bar_y + bar_h), radius=16, fill=BAR_BG)
    if fill_w > 0:
        draw.rounded_rectangle((bar_x, bar_y, bar_x + fill_w, bar_y + bar_h), radius=16, fill=GREEN)

    percent = int(progress * 100)
    draw.text((bar_x, 362), f"{percent}% to next level", font=small_font, fill=GRAY)
    draw.text((CARD_WIDTH - 280, 362), f"Total XP: {total_xp:,}", font=small_font, fill=GRAY)

    output = BytesIO()
    card.convert("RGB").save(output, format="PNG")
    output.seek(0)
    return output
