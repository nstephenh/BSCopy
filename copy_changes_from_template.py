import os
import xml.etree.ElementTree as ET

from util import find_attribute_map, ENTRY_LINK_TYPE, copy_and_add_id, update_all_node_ids

# Press the green button in the gutter to run the script.
if __name__ == '__main__':

    ET.register_namespace("", "http://www.battlescribe.net/schema/catalogueSchema")
    source_tree = ET.parse('/home/nsh/BattleScribe/data/horus-heresy/2022 - LA Template.cattemplate')

    base_path = "/home/nsh/BattleScribe/data/horus-heresy"
    la_files = os.listdir(base_path)

    for file_name in la_files:
        if file_name.startswith("2022 - LA - "):
            file_path = os.path.join(base_path, file_name)
            destination_tree = ET.parse(file_path)
            node_map = {}
            # find the list of all nodes that already exist in the destination tree
            for node in destination_tree.iter():
                bs_id = node.attrib.get("id")
                if bs_id:
                    source_id = find_attribute_map(node)
                    if source_id:
                        node_map[source_id] = bs_id
            # find all the source entries that do not yet exist in the source node and copy it over to the destination tree
            entry_link_node = destination_tree.getroot().find("./{}s".format(ENTRY_LINK_TYPE))
            for node in source_tree.findall("./{}s/{}".format(ENTRY_LINK_TYPE, ENTRY_LINK_TYPE)):
                bs_id = node.attrib.get("id")
                name = node.attrib.get("name")
                if bs_id not in node_map.keys():
                    print("{} should be copied to {}".format(node, file_name))
                    print("  ID: {} Name: {}".format(name, bs_id))
                    # copy the node and add it's new ID to the map, but don't actually change the ID.
                    new_node = copy_and_add_id(node_map, node)
                    # Then add the new node to the destination tree
                    entry_link_node.append(new_node)
            update_all_node_ids(destination_tree.iter(), node_map)
            destination_tree.write(file_path)
