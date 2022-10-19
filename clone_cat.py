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

    node_map = {}  # Dictionary of input IDs to output IDs
    ET.register_namespace("", "http://www.battlescribe.net/schema/catalogueSchema")
    tree = ET.parse('/home/nsh/BattleScribe/data/horus-heresy/2022 - LA - Blood Angels.cat')
    tree2 = deepcopy(tree)
    # Find all nodes in the tree with IDs and make duplicates of each node.
    for node in tree.iter():
        bs_id = node.attrib.get("id")
        if bs_id:
            node_map[bs_id] = get_random_bs_id()
    # Update all nodes in copy 2
    for node in tree2.iter():
        bs_id = node.attrib.get("id")
        if bs_id:
            node.attrib["id"] = node_map[bs_id]
            target_id = node.attrib.get("id")
            if target_id and target_id in node_map.keys():
                node.attrib["targetId"] = node_map[target_id]
            commentNode = node.find(COMMENT_NODE_TYPE)
            if commentNode is not None:
                print(commentNode.text)
            else:
                commentNode = ET.SubElement(node, COMMENT_NODE_TYPE)
                commentNode.text = ""
            commentNode.text += "\n {}{}".format(ID_IDENTIFIER, bs_id)
            if target_id:
                commentNode.text += "\n {}{}".format(TID_IDENTIFIER, target_id)

    tree2.write("/home/nsh/BattleScribe/data/horus-heresy/2022 - LA - AAAAAAA MARINES.cat")

    print(node_map)
    print(len(node_map))
