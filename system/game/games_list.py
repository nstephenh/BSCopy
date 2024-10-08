from system.game.game import Game
from system.game.heresy import Heresy

from system.game.oldworld import OldWorld

games = [
    OldWorld(),
    Heresy(),
]


def get_game(system_name, game_constant=None) -> 'Game':
    for game in games:
        if game.SYSTEM_NAME == system_name or game.GAME_FORMAT_CONSTANT == game_constant:
            return game

    if game_constant is None:
        print("Using generic game spec. Some features may not work")
        return Game()

    raise ValueError(f"Game {game_constant} not defined")
