import os
import uuid
import xml.etree.ElementTree as ET
from copy import deepcopy

from util.generate_util import update_all_node_ids, add_new_id


# Press the green button in the gutter to run the script.

def clone_cat(output_name, assign_ids_to_mods_and_cons=False, generate_map_comments=True):
    node_map = {}  # Dictionary of input IDs to output IDs
    ET.register_namespace("", "http://www.battlescribe.net/schema/catalogueSchema")
    tree = ET.parse(os.path.expanduser('~/BattleScribe/data/horus-heresy/2022 - LA - Blood Angels.cat'))
    tree2 = deepcopy(tree)

    # Find all nodes in the tree with IDs and add them to them map.
    for node in tree.iter():
        add_new_id(node_map, node)

    update_all_node_ids(tree2.iter(), node_map,
                        generate_map_comments=generate_map_comments,
                        assign_ids_to_mods_and_cons=assign_ids_to_mods_and_cons)

    tree2.write(os.path.expanduser('~/BattleScribe/data/horus-heresy/{}'.format(output_name)))


if __name__ == '__main__':
    clone_cat("2022 - LA Test.cat")
