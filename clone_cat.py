import uuid
import xml.etree.ElementTree as ET
from copy import deepcopy

from util import make_comment

ID_IDENTIFIER = "COPIED_FROM_ID_"
TID_IDENTIFIER = "COPIED_FROM_TID_"


def get_random_bs_id():
    return str(uuid.uuid4())[4:23]


# Press the green button in the gutter to run the script.
if __name__ == '__main__':

    map_in_comments = True
    node_map = {}  # Dictionary of input IDs to output IDs
    ET.register_namespace("", "http://www.battlescribe.net/schema/catalogueSchema")
    tree = ET.parse('/home/nsh/BattleScribe/data/horus-heresy/2022 - LA - Blood Angels.cat')
    tree2 = deepcopy(tree)


    def map_tag(source_node, attribute_name):
        bs_id = source_node.attrib.get(attribute_name)
        if bs_id and bs_id in node_map.keys():
            source_node.attrib[attribute_name] = node_map[bs_id]
            if map_in_comments:
                make_comment(source_node, attribute_name, bs_id)


    # Find all nodes in the tree with IDs and add them to them map.
    for node in tree.iter():
        bs_id = node.attrib.get("id")
        if bs_id:
            node_map[bs_id] = get_random_bs_id()

    for node in tree2.iter():
        map_tag(node, "id")
        map_tag(node, "targetId")
        map_tag(node, 'scope')
        map_tag(node, 'childId')
        map_tag(node, 'field')

    tree2.write("/home/nsh/BattleScribe/data/horus-heresy/2022 - LA Test.cat")

    print(node_map)
    print(len(node_map))
