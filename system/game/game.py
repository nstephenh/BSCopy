import settings


class Game:
    # Generic game class
    GAME_FORMAT_CONSTANT = ""
    SYSTEM_NAME = ""  # What does this repo check out as by default
    ProfileLocator = "Troop Type:"

    default_settings = settings.default_settings

    UNIT_PROFILE_TABLE_HEADERS: list[str] = None

    WEAPON_PROFILE_TABLE_HEADERS: list[str] = []

    OPTIONS = "Options"

    MIDDLE_IN_2_COLUMN = False

    ENDS_AFTER_SPECIAL_RULES = False

    FIRST_PARAGRAPH_IS_FLAVOR = False

    COULD_HAVE_STAGGERED_HEADERS = False
