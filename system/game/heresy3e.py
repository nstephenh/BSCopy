from system.constants import GameImportSpecs
from system.game.game import Game


class Heresy3e(Game):
    GAME_FORMAT_CONSTANT = GameImportSpecs.HERESY3E
    SYSTEM_NAME = "horus-heresy-3rd-edition"

    POINTS_NAME = "Point(s)"
    POINTS_ID = "9893-c379-920b-8982"

    ProfileLocator = "unit composition:"

    UNIT_PROFILE_TABLE_HEADER_OPTIONS = {
        "Profile":
            {"raw": ["M", "WS", "BS", "S", "T", "W", "I", "A", "LD", "CL", "WP", "IN", "SAV", "INV"],
             "full": ["M", "WS", "BS", "S", "T", "W", "I", "A", "LD", "CL", "WP", "IN", "SAV", "INV"],
             },
        "Vehicle":
            {"raw": ["M", "BS", "Front", "Side", "Rear", "HP", "Capacity"],
             "full": ["M", "BS", "Front Armour", "Side Armour", "Rear Armour", "HP", "Transport Capacity"],
             },
        "Knight":
            {"raw": ["M", "WS", "BS", "Front", "Rear", "I", "A", "HP"],
             "full": ["M", "WS", "BS", "Front", "Rear", "I", "A", "HP"],
             },
    }

    MODEL_TYPE_CHARACTERISTIC = "Type"

    WARGEAR_PROFILE_NAME = "Wargear"

    WEAPON_PROFILE_TABLE_HEADER_OPTIONS = {
        "Ranged Weapon":
            {"raw": ["R", "FP", "RS", "AP", "D", "Special Rules", "Traits"],
             "full": ["R", "FP", "RS", "AP", "D", "Special Rules", "Traits"],
             },
        "Melee Weapon":
            {"raw": ["IM", "AM", "SM", "AP", "D", "Special Rules", "Traits"],
             "full": ["IM", "AM", "SM", "AP", "D", "Special Rules", "Traits"],
             },
    }

    FIRST_PARAGRAPH_IS_FLAVOR = True

    NUM_WEAPON_HEADERS_THAT_ARE_TEXT = 2  # "Special Rules" and "Traits"

    DASHED_WEAPON_MODES = True

    UNIT_SUBHEADINGS: list[str] = ["WARGEAR",
                                   "TRAITS",
                                   "SPECIAL RULES",
                                   "TYPE",
                                   "OPTIONS",
                                   "ACCESS POINTS"
                                   ]  # Not doing "Using this Unit" (pre profiles, post-flavor text)

    SUBHEADINGS_AFTER_2_COL_SECTION: list[str] = ["OPTIONS",
                                                  "ACCESS POINTS"]

    # HH3 has a 2 column section but then after that each section splits into 2 columns, wrapping independently.
    SUBHEADINGS_AFTER_2_COL_ARE_2_COL = True

    BATTLEFIELD_ROLES: list[str] = [
        "Warlord",
        "Lord of War",
        "High Command",
        "Command",
        "Retinue",
        "Elites",
        "War-engine",
        "Troops",
        "Support",
        "Transport",
        "Heavy Assault",
        "Heavy Transport",
        "Armour",
        "Recon",
        "Fast Attack",
        "Fortification",
    ]

    LEGIONS: list[str] = [
        "Ultramarines", "Salamanders", "White Scars", "Iron Hands", "Dark Angels", "Space Wolves",
        "Raven Guard", "Blood Angels", "Imperial Fists", "Sons of Horus",
        "Emperor's Children", "Iron Warriors", "World Eaters", "Night Lords", "Death Guard", "Thousand Sons",
        "Word Bearers", "Alpha Legion"
    ]

    FACTIONS: list[str] = LEGIONS.copy() + ["Legiones Astartes", "Mechanicum", "Anathema Psykana",
                                            "Questoris Household",
                                            "Agents of the Divisio Assassinorum", "Legio Custodes", "Solar Auxilia"]

    FACTION_TO_PRIME_SELECTOR_ID: dict[str, str] = {"Legiones Astartes": "a396-b846-c263-6767",
                                                    "Mechanicum": "4ae1-f3b2-e1c8-165f",
                                                    "Anathema Psykana": "5f88-9f8a-5fef-2a71",
                                                    "Questoris Household": "682c-89df-2b40-9302",
                                                    "Agents of the Divisio Assassinorum": "",
                                                    "Legio Custodes": "6f4b-388a-b001-abde",
                                                    "Solar Auxilia": "8180-ce7c-accf-f232",
                                                    }

    def get_prime_selector(self, faction):
        if faction in self.FACTION_TO_PRIME_SELECTOR_ID.keys():
            return self.FACTION_TO_PRIME_SELECTOR_ID[faction]
        else:
            if faction in self.LEGIONS:
                return self.FACTION_TO_PRIME_SELECTOR_ID["Legiones Astartes"]
