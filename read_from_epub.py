from book_reader.import_constants import SETTINGS, ACTIONS
from system.system import System

if __name__ == '__main__':
    system = System('Warhammer-The-Old-World', include_raw=True,
                    raw_import_settings={
                        SETTINGS.first_paragraph_is_flavor: True,
                        SETTINGS.actions: [
                            ACTIONS.load_special_rules,
                        ]
                    })
