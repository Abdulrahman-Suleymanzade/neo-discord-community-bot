import random
import math

MIN_XP = 15
MAX_XP = 40


def generate_xp() -> int:
    return random.randint(MIN_XP, MAX_XP)


def calculate_level(xp: int) -> int:
    return int(math.sqrt(xp // 100))


def xp_for_next_level(level: int) -> int:
    return ((level + 1) ** 2) * 100
