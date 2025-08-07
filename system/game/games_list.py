from system.game.game import Game
from system.game.heresy2nd import Heresy2nd
from system.game.heresy3e import Heresy3e

from system.game.oldworld import OldWorld

games = [
    OldWorld(),
    Heresy2nd(),
    Heresy3e(),
]


def get_game(system_name, game_constant=None) -> 'Game':
    for game in games:
        if game.SYSTEM_NAME == system_name or game.GAME_FORMAT_CONSTANT == game_constant:
            return game

    if game_constant is None:
        print("Using generic game spec. Some features may not work")
        return Game()

    raise ValueError(f"Game {game_constant} not defined")
