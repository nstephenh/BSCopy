from system.constants import GameImportSpecs, SpecialRulesType, SystemSettingsKeys
from system.game.game import Game


class OldWorld(Game):
    # Generic game class
    GAME_FORMAT_CONSTANT = GameImportSpecs.OLDWORLD
    SYSTEM_NAME = "Warhammer-The-Old-World"

    ProfileLocator = "Troop Type:"

    default_settings = {
        SystemSettingsKeys.SPECIAL_RULE_TYPE: SpecialRulesType.PROFILE_SPECIAL_RULE,
        SystemSettingsKeys.WEAPON_AS_DESCRIPTION: False,
    }
    UNIT_PROFILE_TABLE_HEADER_OPTIONS = {
        "Unit":
            {"raw": ["M", "WS", "BS", "S", "T", "W", "I", "A", "Ld", "Points"],
             "full": ["M", "WS", "BS", "S", "T", "W", "I", "A", "Ld", "Points"],
             },
    }
    WEAPON_PROFILE_TABLE_HEADERS = ["R", "S", "AP", "Special Rules"]

    COMBINED_ARTILLERY_PROFILE = True

    OPTIONS = "Options:"

    MIDDLE_IN_2_COLUMN = False

    ENDS_AFTER_SPECIAL_RULES = True

    FIRST_PARAGRAPH_IS_FLAVOR = True
    IN_DATASHEET_FIRST_PARAGRAPH_IS_FLAVOR = True

    UNIT_SUBHEADINGS: list[str] = ["Troop Type:",
                                   "Base Size:",
                                   "Unit Size:",
                                   "Armour Value:",
                                   "Equipment:",
                                   "Magic:",
                                   "Options:",
                                   "Special Rules:",
                                   ]
