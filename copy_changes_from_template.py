import os
import xml.etree.ElementTree as ET

from util import find_source_id, SELECTION_ENTRY_TYPE, ENTRY_LINK_TYPE

# Press the green button in the gutter to run the script.
if __name__ == '__main__':

    ET.register_namespace("", "http://www.battlescribe.net/schema/catalogueSchema")
    source_tree = ET.parse('/home/nsh/BattleScribe/data/horus-heresy/2022 - LA Template.cattemplate')

    base_path = "/home/nsh/BattleScribe/data/horus-heresy"
    la_files = os.listdir(base_path)

    for file_name in la_files:
        if file_name.startswith("2022 - LA - "):
            file_path = os.path.join(base_path, file_name)
            tree2 = ET.parse(file_path)
            node_map = {}
            for node in tree2.iter():
                bs_id = node.attrib.get("id")
                if bs_id:
                    source_id = find_source_id(node)
                    if source_id:
                        node_map[source_id] = bs_id
            for node in source_tree.findall("./{}s/{}".format(ENTRY_LINK_TYPE, ENTRY_LINK_TYPE)):
                bs_id = node.attrib.get("id")
                name = node.attrib.get("name")
                if bs_id not in node_map.keys():
                    print("{} should be copied to {}".format(node, file_name))
                    print("  ID: {} Name: {}".format(name, bs_id))
