import os
import uuid
import xml.etree.ElementTree as ET
from copy import deepcopy

from util import update_all_node_ids, add_new_id


def get_random_bs_id():
    return str(uuid.uuid4())[4:23]


# Press the green button in the gutter to run the script.
if __name__ == '__main__':

    generate_map_comments = False
    node_map = {}  # Dictionary of input IDs to output IDs
    ET.register_namespace("", "http://www.battlescribe.net/schema/catalogueSchema")
    tree = ET.parse(os.path.expanduser('~/BattleScribe/data/horus-heresy/2022 - LA - Blood Angels.cat'))
    tree2 = deepcopy(tree)

    # Find all nodes in the tree with IDs and add them to them map.
    for node in tree.iter():
        add_new_id(node_map, node)

    update_all_node_ids(tree2.iter(), node_map, assign_ids_to_mods_and_cons=True)

    tree2.write(os.path.expanduser('~/BattleScribe/data/horus-heresy/2022 - LA Test.cat'))

    print(node_map)
    print(len(node_map))
