from book_reader.constants import ReadSettingsKeys, Actions
from system.constants import SystemSettingsKeys, GameImportSpecs
from system.system import System

if __name__ == '__main__':
    system = System('horus-heresy-3rd-edition',
                    settings={
                        SystemSettingsKeys.GAME_IMPORT_SPEC: GameImportSpecs.HERESY2E,
                    },
                    include_raw=False,
                    )
    system.save_system()