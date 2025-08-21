import settings


class Game:
    # Generic game class
    GAME_FORMAT_CONSTANT = ""
    SYSTEM_NAME = ""  # What does this repo check out as by default
    ProfileLocator = "Troop Type:"

    default_settings = settings.default_settings

    UNIT_PROFILE_TABLE_HEADER_OPTIONS: {str: {str: [str]}} = {}  # "name": {"raw": [list], "full": [list]}

    WEAPON_PROFILE_TABLE_HEADER_OPTIONS: {str: {str: [str]}} = {}  # "name": {"raw": [list], "full": [list]}

    @property  # Deprecated for options version, left for backwards compat
    def WEAPON_PROFILE_TABLE_HEADERS(self) -> list[str]:
        if not self.WEAPON_PROFILE_TABLE_HEADER_OPTIONS:
            raise Exception("No weapon profile headers defined")
        return self.WEAPON_PROFILE_TABLE_HEADER_OPTIONS["Weapon"]['raw']

    @property  # Deprecated for options version, left for backwards compat
    def WEAPON_PROFILE_TABLE_HEADERS_FULL(self) -> list[str]:
        if not self.WEAPON_PROFILE_TABLE_HEADER_OPTIONS:
            raise Exception("No weapon profile headers defined")
        return self.WEAPON_PROFILE_TABLE_HEADER_OPTIONS["Weapon"]['full']

    NUM_WEAPON_HEADERS_THAT_ARE_TEXT = 1  # Normally just "Special Rules"

    OPTIONS = "Options"

    MIDDLE_IN_2_COLUMN = False

    ENDS_AFTER_SPECIAL_RULES = False

    FIRST_PARAGRAPH_IS_FLAVOR = False
    IN_DATASHEET_FIRST_PARAGRAPH_IS_FLAVOR = False

    COULD_HAVE_STAGGERED_HEADERS = False

    UNIT_SUBHEADINGS: list[str] = []  # MUST BE IN ORDER

    SUBHEADINGS_AFTER_2_COL_SECTION: list[str] = []  # MUST BE IN ORDER

    # Has a 2 column section but then after that each section splits into 2 columns, wrapping independently.
    SUBHEADINGS_AFTER_2_COL_ARE_2_COL = False

    SUBHEADINGS_ON_SAME_LINE = False

    SUBHEADING_SEPARATORS: str = None  # Bullets, commas, or Commas and "and"

    COMBINED_ARTILLERY_PROFILE = False

    DASHED_WEAPON_MODES = False

    NAME_HAS_DOTS: bool = False

    FORCE_ORG_IN_FLAVOR: bool = False

    category_book_to_full_name_map: dict[str, str] = {}

    BATTLEFIELD_ROLES: list[str] = []

    FACTIONS: list[str] = []

    def get_full_characteristic_name(self, characteristic_name, profile_type: str = None):
        if profile_type in self.WEAPON_PROFILE_TABLE_HEADER_OPTIONS:
            characteristic_list = self.WEAPON_PROFILE_TABLE_HEADER_OPTIONS[profile_type]['raw']
            full_characteristic_list = self.WEAPON_PROFILE_TABLE_HEADER_OPTIONS[profile_type]['full']
        if profile_type in self.UNIT_PROFILE_TABLE_HEADER_OPTIONS:
            characteristic_list = self.UNIT_PROFILE_TABLE_HEADER_OPTIONS[profile_type]['raw']
            full_characteristic_list = self.UNIT_PROFILE_TABLE_HEADER_OPTIONS[profile_type]['full']
        full_name = characteristic_name
        if characteristic_name in characteristic_list and len(full_characteristic_list):
            i = characteristic_list.index(characteristic_name)
            full_name = full_characteristic_list[i]
        return full_name
