from system.constants import GameImportSpecs
from system.game.game import Game


class Heresy(Game):
    GAME_FORMAT_CONSTANT = GameImportSpecs.HERESY
    SYSTEM_NAME = "horus-heresy"

    ProfileLocator = "Unit Composition"

    MIDDLE_IN_2_COLUMN = True

    FIRST_PARAGRAPH_IS_FLAVOR = True
