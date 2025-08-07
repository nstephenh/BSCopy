from system.constants import GameImportSpecs
from system.game.game import Game


class Heresy3e(Game):
    GAME_FORMAT_CONSTANT = GameImportSpecs.HERESY3E
    SYSTEM_NAME = "horus-heresy-3rd-edition"

    ProfileLocator = "UNIT COMPOSITION:"

    UNIT_PROFILE_TABLE_HEADER_OPTIONS = {
        "Profile":
            {"raw": ["M", "WS", "BS", "S", "T", "W", "I", "A", "LD", "CL", "WP", "IN", "SAV", "INV"],
             },
    }

    UNIT_SUBHEADINGS: list[str] = ["WARGEAR", "SPECIAL RULES",
                                   "TRAITS", "TYPE",
                                   ]
