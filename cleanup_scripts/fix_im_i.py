import json
import sys

from system.system import System

if __name__ == '__main__':
    system_name = "horus-heresy-3rd-edition"

    try:
        system_name = sys.argv[1]
    except IndexError:
        pass

    system = System(system_name)

    for profile_node in system.nodes_with_ids.filter(lambda node: node.tag == 'profile'):
        characteristics = profile_node.get_profile_dict()
        if characteristics.get("IM", None) == "1":
            print("Found IM == 1 profile: ", profile_node.name, profile_node.id)
            characteristics["IM"] = "I"
            characteristics.pop("Name")
            profile_node.set_characteristics_from_dict(characteristics, profile_node.type_name)

    system.save_system()
