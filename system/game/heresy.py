from system.constants import GameImportSpecs
from system.game.game import Game


class Heresy(Game):
    GAME_FORMAT_CONSTANT = GameImportSpecs.HERESY
    SYSTEM_NAME = "horus-heresy"

    ProfileLocator = "Unit Composition"

    UNIT_PROFILE_TABLE_HEADERS = ["M", "WS", "BS", "S", "T", "W", "I", "A", "Ld", "Sv"]

    ALT_UNIT_PROFILE_TABLE_HEADERS: list[str] = ["M", "BS", "Front", "Side", "Rear", "HP", "Capacity"]
    ALT_UNIT_PROFILE_TABLE_HEADERS_FULL: list[str] = ["M", "BS", "Front", "Side", "Rear", "HP", "Transport Capacity"]

    ALT_PROFILE_NAME = "Vehicle"

    WEAPON_PROFILE_TABLE_HEADERS = ["Range", "Str", "AP", "Type"]

    MIDDLE_IN_2_COLUMN = True

    FIRST_PARAGRAPH_IS_FLAVOR = True

    COULD_HAVE_STAGGERED_HEADERS = True  # In some fan supplements, the headers may not line up because of images.

    UNIT_SUBHEADINGS: list[str] = ["Unit Composition", "Unit Type", "Wargear", "Special Rules",
                                   "Dedicated Transport",
                                   "Access Points",
                                   "Options"]

    SUBHEADINGS_ON_SAME_LINE = True

    NAME_HAS_DOTS: bool = True

    FORCE_ORG_IN_FLAVOR: bool = True
