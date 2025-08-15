from book_reader.raw_entry import RawModel
from system.constants import SystemSettingsKeys, GameImportSpecs
from system.system import System
from util.text_utils import read_type_and_subtypes

if __name__ == '__main__':

    system = System('horus-heresy-3rd-edition',
                    settings={
                        SystemSettingsKeys.GAME_IMPORT_SPEC: GameImportSpecs.HERESY3E,
                    },
                    )
    model_count = 0
    models_with_profiles_count = 0
    models_without_profiles = []
    for model_node in system.nodes_with_ids.filter(lambda x: x.type == "selectionEntry:model"):
        print(model_node)
        model_count += 1
        profile_node = model_node.get_profile_node()
        if profile_node is None:
            models_without_profiles.append(str(model_node))
            continue
        profile_dict = profile_node.get_profile_dict()
        models_with_profiles_count += 1
        unit_type_text = profile_dict.get("Type")
        if unit_type_text is None:
            models_without_profiles.append(str(model_node))
            continue
        type_and_subtypes = read_type_and_subtypes(unit_type_text)

        print(type_and_subtypes)
        # Make a rawModel so we can set types and subtypes
        raw_model = RawModel(None, model_node.name, None, None, None)
        raw_model.type_and_subtypes = type_and_subtypes
        model_node.set_types_and_subtypes(raw_model)

        print()
    print(f"{models_with_profiles_count} of {model_count} set")
    print(models_without_profiles)
    system.save_system()
