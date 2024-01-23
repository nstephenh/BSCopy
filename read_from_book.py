from book_reader.constants import ReadSettingsKeys, Actions
from system.constants import SpecialRulesType, SystemSettingsKeys
from system.system import System

if __name__ == '__main__':
    system = System('Warhammer-The-Old-World',
                    settings={
                        SystemSettingsKeys.SPECIAL_RULE_TYPE: SpecialRulesType.PROFILE_SPECIAL_RULE,
                        SystemSettingsKeys.WEAPON_AS_DESCRIPTION: True,
                    },
                    include_raw=True,
                    raw_import_settings={
                        ReadSettingsKeys.FIRST_PARAGRAPH_IS_FLAVOR: True,
                        ReadSettingsKeys.ACTIONS: [
                            Actions.LOAD_SPECIAL_RULES,
                            Actions.LOAD_WEAPON_PROFILES,
                        ],
                    })
    system.save_system()
