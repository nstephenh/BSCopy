from book_reader.constants import ReadSettingsKeys, Actions
from system.constants import SystemSettingsKeys, GameImportSpecs
from system.system import System

if __name__ == '__main__':
    system = System('horus-heresy-panoptica',
                    settings={
                        SystemSettingsKeys.GAME_IMPORT_SPEC: GameImportSpecs.HERESY,
                    },
                    include_raw=False,
                    )
    system.save_system()