from system.constants import GameImportSpecs
from system.game.game import Game
from system.game.heresy import Heresy
from system.game.oldworld import OldWorld

games = {
    GameImportSpecs.OLDWORLD: OldWorld(),
    GameImportSpecs.HERESY: Heresy(),
}


def get_game(system_name, game_constant=None) -> 'Game':
    if game_constant is None:
        for game in games.values():
            if game.SYSTEM_NAME == system_name:
                return game
        raise ValueError(f"Game system {system_name} has no default import spec")

    if game_constant in games:
        return games[game_constant]
    raise ValueError(f"Game {game_constant} not defined")
