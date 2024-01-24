from system.constants import GameImportSpecs
from system.game.game import Game


class Heresy(Game):
    # Generic game class
    GAME_FORMAT_CONSTANT = GameImportSpecs.HERESY
    SYSTEM_NAME = "horus-heresy"

    ProfileLocator = "Unit Composition"
