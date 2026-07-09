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

def calculate_prestige(level: int) -> int:
    if level < 100:
        return 0
    return ((level - 100) // 50) + 1


def next_prestige_level(level: int) -> int:
    if level < 100:
        return 100
    return 100 + (calculate_prestige(level) * 50)
