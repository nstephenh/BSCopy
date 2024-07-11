from book_reader.constants import ReadSettingsKeys, Actions
from system.constants import SystemSettingsKeys, GameImportSpecs
from system.system import System

if __name__ == '__main__':
    system = System('horus-heresy-panoptica',
                    settings={
                        SystemSettingsKeys.GAME_IMPORT_SPEC: GameImportSpecs.HERESY,
                    },
                    include_raw=True,
                    raw_import_settings={
                        ReadSettingsKeys.FIRST_PARAGRAPH_IS_FLAVOR: True,
                        ReadSettingsKeys.ACTIONS: [
                            Actions.DUMP_TO_JSON,
                            Actions.LOAD_SPECIAL_RULES,
                            Actions.LOAD_WEAPON_PROFILES,
                            Actions.LOAD_UNITS,
                        ],
                    })
    system.save_system()
    for error in system.errors:
        print(error)
    print(f"Error count: {len(system.errors)}")
