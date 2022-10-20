import copy
import os
import xml.etree.ElementTree as ET

from util import find_attribute_map, ENTRY_LINK_TYPE, update_all_node_ids, add_new_id

# Press the green button in the gutter to run the script.
if __name__ == '__main__':

    ET.register_namespace("", "http://www.battlescribe.net/schema/catalogueSchema")

    overwrite = True
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
            entry_links_node = destination_tree.getroot().find("./{}s".format(ENTRY_LINK_TYPE))
            if overwrite:
                entry_links_node.clear()
            # find all the source entries that do not yet exist in the source node
            # and copy it over to the destination tree
            for node in source_tree.findall("./{}s/{}".format(ENTRY_LINK_TYPE, ENTRY_LINK_TYPE)):
                bs_id = node.attrib.get("id")
                name = node.attrib.get("name")
                if bs_id not in node_map.keys():
                    print("Copying {} to {}".format(node, file_name))
                    print("  ID: {} Name: {}".format(name, bs_id))
                    new_node = copy.deepcopy(node)
                    # Add a new ID to the map, update_all_nodes will modify the node.
                    add_new_id(node_map, node)
                    # Then add the new node to the destination tree
                    entry_links_node.append(new_node)
                # Overwrite existing node contents (will map child nodes)
                elif overwrite:
                    print("Updating {} in {}".format(name, file_name))
                    node_copy = copy.deepcopy(node)
                    node_copy.clear()
                    for key, value in node.attrib.items():
                        node_copy.set(key, value)  # Copy over attributes we just cleared.
                    # The node is already mapped through it's ID, but we want to copy the children.
                    for child in node:
                        for fam in child:
                            add_new_id(node_map, fam)  # Change each child and descendant ID
                        # Copy child nodes to the copy
                        node_copy.append(copy.deepcopy(child))
                    # Add new node to output file
                    entry_links_node.append(node_copy)

            update_all_node_ids(destination_tree.iter(), node_map)
            destination_tree.write(file_path)
