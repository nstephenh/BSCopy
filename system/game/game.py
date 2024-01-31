import settings


class Game:
    # Generic game class
    GAME_FORMAT_CONSTANT = ""
    SYSTEM_NAME = ""  # What does this repo check out as by default
    ProfileLocator = "Troop Type:"

    default_settings = settings.default_settings

    UNIT_PROFILE_TABLE_HEADERS: list[str] = []

    ALT_UNIT_PROFILE_TABLE_HEADERS: list[str] = []
    ALT_UNIT_PROFILE_TABLE_HEADERS_FULL: list[str] = []

    ALT_PROFILE_NAME = None

    WEAPON_PROFILE_TABLE_HEADERS: list[str] = []

    OPTIONS = "Options"

    MIDDLE_IN_2_COLUMN = False

    ENDS_AFTER_SPECIAL_RULES = False

    FIRST_PARAGRAPH_IS_FLAVOR = False
    IN_DATASHEET_FIRST_PARAGRAPH_IS_FLAVOR = False

    COULD_HAVE_STAGGERED_HEADERS = False

    UNIT_SUBHEADINGS: list[str] = []  # MUST BE IN ORDER

    SUBHEADINGS_ON_SAME_LINE = False

    SUBHEADING_SEPARATORS: str = None  # Bullets, commas, or Commas and "and"

    COMBINED_ARTILLERY_PROFILE = False

    NAME_HAS_DOTS: bool = False

    FORCE_ORG_IN_FLAVOR: bool = False
