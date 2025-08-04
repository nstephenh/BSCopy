import argparse

from book_reader.raw_entry import RawModel
from system.constants import SystemSettingsKeys, GameImportSpecs
from system.node import Node
from system.system import System
from xml.etree import ElementTree as ET

from util.element_util import get_description
from util.log_util import print_styled, STYLES, get_diff, prompt_y_n

if __name__ == '__main__':

    system = System('horus-heresy',
                    settings={
                        SystemSettingsKeys.GAME_IMPORT_SPEC: GameImportSpecs.HERESY2E,
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
        unit_type_text = profile_dict.get("Unit Type")
        if unit_type_text is None:
            models_without_profiles.append(str(model_node))
            continue
        print(unit_type_text)
        if "(" in unit_type_text:
            type_and_subtypes = [unit_type_text.split("(")[0].strip()]
            type_and_subtypes += [text.strip() for text in unit_type_text.split("(")[1][:-1].strip().split(",")]
        else:
            type_and_subtypes = [unit_type_text.strip()]

        print(type_and_subtypes)
        # Make a rawModel so we can set types and subtypes
        raw_model = RawModel(None, model_node.name, None, None, None)
        raw_model.type_and_subtypes = type_and_subtypes
        model_node.set_types_and_subtypes(raw_model)

        print()
    print(f"{models_with_profiles_count} of {model_count} set")
    print(models_without_profiles)
    system.save_system()
