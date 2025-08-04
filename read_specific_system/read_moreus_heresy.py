from book_reader.constants import ReadSettingsKeys, Actions
from system.constants import SystemSettingsKeys, GameImportSpecs
from system.system import System

if __name__ == '__main__':
    system = System('horus-heresy-panoptica',
                    settings={
                        SystemSettingsKeys.GAME_IMPORT_SPEC: GameImportSpecs.HERESY2E,
                    },
                    include_raw=True,
                    raw_import_settings={
                        ReadSettingsKeys.FIRST_PARAGRAPH_IS_FLAVOR: True,
                        ReadSettingsKeys.ACTIONS: [
                            Actions.DUMP_TO_JSON,
                            Actions.LOAD_SPECIAL_RULES,
                            Actions.MODIFY_WEAPONS,  # Modify an existing profiles
                            Actions.LOAD_WEAPON_PROFILES,  # Add any new profiles
                            Actions.LOAD_UNITS,
                        ],
                    })
    system.save_system()
    for error in system.errors:
        print(error)
    print(f"Error count: {len(system.errors)}")
