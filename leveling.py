import random
import math

MIN_XP = 15
MAX_XP = 40
XP_MULTIPLIER = 25


def generate_xp() -> int:
    return random.randint(MIN_XP, MAX_XP)


def calculate_level(xp: int) -> int:
    return int(math.sqrt(xp / XP_MULTIPLIER))


def xp_for_next_level(level: int) -> int:
    return ((level + 1) ** 2) * XP_MULTIPLIER


def xp_for_level(level: int) -> int:
    return (level ** 2) * XP_MULTIPLIER
