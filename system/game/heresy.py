from system.constants import GameImportSpecs
from system.game.game import Game


class Heresy(Game):
    GAME_FORMAT_CONSTANT = GameImportSpecs.HERESY
    SYSTEM_NAME = "horus-heresy"

    ProfileLocator = "Unit Composition"

    UNIT_PROFILE_TABLE_HEADER_OPTIONS = {
        "Unit":
            {"raw": ["M", "WS", "BS", "S", "T", "W", "I", "A", "Ld", "Sv"],
             "full": ["Move", "WS", "BS", "S", "T", "W", "I", "A", "Ld", "Save"],
             },
        "Vehicle":
            {"raw": ["M", "BS", "Front", "Side", "Rear", "HP", "Capacity"],
             "full": ["Move", "BS", "Front", "Side", "Rear", "HP", "Transport Capacity"],
             },
        "Knights and Titans":
            {"raw": ["M", "WS", "BS", "S", "Front", "Side", "Rear", "I", "A", "HP"],
             "full": ["Move", "WS", "BS", "S", "Front", "Side", "Rear", "I", "A", "HP"],
             },
    }

    WEAPON_PROFILE_TABLE_HEADERS = ["Range", "Str", "AP", "Type"]
    WEAPON_PROFILE_TABLE_HEADERS_FULL: list[str] = ["Range", "Strength", "AP", "Type"]

    MIDDLE_IN_2_COLUMN = True

    FIRST_PARAGRAPH_IS_FLAVOR = True

    COULD_HAVE_STAGGERED_HEADERS = True  # In some fan supplements, the headers may not line up because of images.

    UNIT_SUBHEADINGS: list[str] = ["Unit Composition", "Unit Type", "Wargear", "Special Rules",
                                   "Dedicated Transport:",
                                   "Access Points:",
                                   "Options:",
                                   "Options"]  # Check options both with and without colons.

    SUBHEADINGS_ON_SAME_LINE = True

    DASHED_WEAPON_MODES = True

    NAME_HAS_DOTS: bool = True

    FORCE_ORG_IN_FLAVOR: bool = True

    category_book_to_full_name_map: dict[str, str] = {
        # Drop the trailing colon because we strip that from categories
        "HQ": "HQ",
        "ELITES": "Elites",
        "TROOPS": "Troops",
        "DEDICATED": None,  # Dedicated transport doesn't get a primary category
        "FAST ATTACK": "Fast Attack",
        "HEAVY SUPPORT": "Heavy Support",
        "LORDS OF WAR": "Lords of War",
        "PRIMARCH": "Primarch",
        "FORTIFICATION": "Fortification",
    }
