from system.constants import SystemSettingsKeys, GameImportSpecs
from system.system import System

if __name__ == '__main__':

    system = System('horus-heresy-3rd-edition',
                    settings={
                        SystemSettingsKeys.GAME_IMPORT_SPEC: GameImportSpecs.HERESY3E,
                    },
                    )
    for type_category in system.model_types_and_subtypes.values():
        for type_link in system.nodes_with_ids.filter(lambda x: x.target_id == type_category.id):
            se = type_link.parent.parent
            if se.type != "selectionEntry:model":
                type_link.delete()
    system.save_system()
