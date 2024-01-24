from system.constants import GameImportSpecs
from system.game.game import Game


class OldWorld(Game):
    # Generic game class
    GAME_FORMAT_CONSTANT = GameImportSpecs.OLDWORLD
    SYSTEM_NAME = "Warhammer-The-Old-World"

    ProfileLocator = "Troop Type:"

    UNIT_PROFILE_TABLE_HEADERS = ["M", "WS", "BS", "S", "T", "W", "I", "A", "Ld", "Points"]

    WEAPON_PROFILE_TABLE_HEADERS = ["R", "S", "AP", "Special Rules"]
