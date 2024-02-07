from enum import StrEnum


class ReadSettingsKeys(StrEnum):
    FIRST_PARAGRAPH_IS_FLAVOR = 'first_paragraph_is_flavor'
    ACTIONS = "actions"


class Actions(StrEnum):
    DUMP_TO_JSON = 'Dump To JSON'
    LOAD_SPECIAL_RULES = 'Load Special Rules'
    LOAD_WEAPON_PROFILES = 'Load Weapon Profiles'
    LOAD_UNITS = 'Load Units'


class PageTypes(StrEnum):
    FAQ = 'faq_pages'
    SPECIAL_RULES = "special_rule_pages"
    WEAPON_PROFILES = 'weapon_profile_pages'
    UNIT_PROFILES = "unit_profile_pages"
    TYPES_AND_SUBTYPES = "types_and_subtypes_pages"
    WARGEAR = "wargear_pages"
    BLANK_OR_IGNORED = "blank_or_ignored_pages"
