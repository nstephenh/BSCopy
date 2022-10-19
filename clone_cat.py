import uuid
import xml.etree.ElementTree as ET
from copy import deepcopy

COMMENT_NODE_TYPE = "{http://www.battlescribe.net/schema/catalogueSchema}comment"
ID_IDENTIFIER = "COPIED_FROM_ID_"
TID_IDENTIFIER = "COPIED_FROM_TID_"


def get_random_bs_id():
    return str(uuid.uuid4())[4:23]


# Press the green button in the gutter to run the script.
if __name__ == '__main__':

    map_in_comments = False
    node_map = {}  # Dictionary of input IDs to output IDs
    ET.register_namespace("", "http://www.battlescribe.net/schema/catalogueSchema")
    tree = ET.parse('/home/nsh/BattleScribe/data/horus-heresy/2022 - LA - Blood Angels.cat')
    tree2 = deepcopy(tree)


    def map_tag(node, tag_name):
        bs_id = node.attrib.get(tag_name)
        if bs_id and bs_id in node_map.keys():
            node.attrib[tag_name] = node_map[bs_id]
            if map_in_comments:
                commentNode = node.find(COMMENT_NODE_TYPE)
                if commentNode is None:
                    commentNode = ET.SubElement(node, COMMENT_NODE_TYPE)
                    commentNode.text = ""
                commentNode.text += "\n library_{}_{}".format(tag_name, bs_id)


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

    tree2.write("/home/nsh/BattleScribe/data/horus-heresy/2022 - LA Template.cat")

    print(node_map)
    print(len(node_map))
