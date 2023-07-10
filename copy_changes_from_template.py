import copy
import os
import xml.etree.ElementTree as ET

from util import find_comment_value, ENTRY_LINK_TYPE, update_all_node_ids, add_new_id, get_mod_and_con_ids, \
    MODIFIER_TYPE


def copy_changes_from_template(overwrite=False):
    ET.register_namespace("", "http://www.battlescribe.net/schema/catalogueSchema")

    source_tree = ET.parse(os.path.expanduser('~/BattleScribe/data/horus-heresy/2022 - LA Template.cattemplate'))

    base_path = os.path.expanduser('~/BattleScribe/data/horus-heresy')
    la_files = os.listdir(base_path)

    for file_name in la_files:
        if file_name.startswith("2022 - LA - "):
            file_path = os.path.join(base_path, file_name)
            destination_tree = ET.parse(file_path)
            node_map = {}
            # find the list of all nodes that already exist in the destination tree
            for node in destination_tree.iter():
                target_id = node.attrib.get("id")
                if target_id:
                    source_id = find_comment_value(node)
                    if source_id:
                        node_map[source_id] = target_id
            entry_links_node = destination_tree.getroot().find("./{}s".format(ENTRY_LINK_TYPE))
            if overwrite:
                backup_tree = copy.deepcopy(destination_tree)
                entry_links_node.clear()
                # Check existing entries, and copy/update them depending on if they exist.
                for node in backup_tree.findall("./{}s/{}".format(ENTRY_LINK_TYPE, ENTRY_LINK_TYPE)):
                    target_id = node.attrib.get("id")
                    name = node.attrib.get("name")
                    if target_id not in node_map.values():  # Replace existing nodes that are not mapped
                        print("Not touching {} in {}".format(name, file_name))
                        entry_links_node.append(node)
                    else:  # Overwrite existing node contents (will map child nodes)
                        index = list(node_map.values()).index(target_id)
                        bs_id = list(node_map.keys())[index]
                        node = source_tree.find("./{}s/{}[@id='{}']".format(ENTRY_LINK_TYPE, ENTRY_LINK_TYPE, bs_id))
                        print("Updating {} in {}".format(name, file_name))
                        node_copy = copy.deepcopy(node)
                        node_copy.clear()
                        for key, value in node.attrib.items():
                            node_copy.set(key, value)  # Copy over attributes we just cleared.
                        # The node is already mapped through it's ID, but we want to copy the children.
                        for child in node:
                            for fam in child:
                                add_new_id(node_map, fam)  # Change each child and descendant ID?
                                # TODO: Does this actually do anything?
                            # Copy child nodes to the copy
                            node_copy.append(copy.deepcopy(child))
                        # Add new node to output file
                        entry_links_node.append(node_copy)
            else:
                backup_tree = copy.deepcopy(destination_tree)
                # Check which nodes exist in the destination tree
                for destination_node in destination_tree.findall("./{}s/{}".format(ENTRY_LINK_TYPE, ENTRY_LINK_TYPE)):
                    target_id = legion_source_node.attrib.get("id")
                    name = legion_source_node.attrib.get("name")
                    if target_id in node_map.values():
                        index = list(node_map.values()).index(target_id)
                        bs_id = list(node_map.keys())[index]
                        source_node = source_tree.find(
                            "./{}s/{}[@id='{}']".format(ENTRY_LINK_TYPE, ENTRY_LINK_TYPE, bs_id))
                        legion_source_node = backup_tree.find(
                            "./{}s/{}[@id='{}']".format(ENTRY_LINK_TYPE, ENTRY_LINK_TYPE, bs_id))

                        destination_node.clear()
                        for key, value in node.attrib.items():
                            node_copy.set(key, value)  # Copy over attributes we just cleared.

                        # Check that all categories are the same between source and target?

                        # Restore non-modifier children
                        for child in legion_source_node:
                            if child.tag != (MODIFIER_TYPE + "s"):
                                destination_node.append(copy.deepcopy(child))
                        modifiers_node = ET.SubElement(destination_node, tag=(MODIFIER_TYPE + "s"))

                        for mod_node in source_node.findall("{}".format(MODIFIER_TYPE)):
                            modifiers_node.append(deep_copy=mod_node)

                        # copy mods from legion_source_node

                        # find or create a root "or" block

                        # drop all nodes in that or block

                        source_mods_and_cons = get_mod_and_con_ids(source_node.iter())
                        destination_m_and_c = get_mod_and_con_ids(legion_source_node.iter())
                        for node_id in source_mods_and_cons:
                            if node_id not in destination_m_and_c:
                                print("{}'s {} needs updated with {}".format(file_name, name, node_id))

                        # Find all legion specific modifiers and conditions
                        for descendant in source_node.iter():
                            if descendant.tag in [MODIFIER_TYPE, CONDITION_TYPE, CONDITION_GROUP_TYPE]:
                                node_id = find_comment_value(descendant, node_id=True)
                                if node_id is None:
                                    print("{}'s {} adds {}".format(file_name, name, descendant))

            # find all the source entries that do not yet exist in the source node
            # and copy it over to the destination tree
            for node in source_tree.findall("./{}s/{}".format(ENTRY_LINK_TYPE, ENTRY_LINK_TYPE)):
                target_id = node.attrib.get("id")
                name = node.attrib.get("name")
                if target_id not in node_map.keys():
                    print("Copying {} to {}".format(name, file_name))
                    new_node = copy.deepcopy(node)
                    # Add a new ID to the map, update_all_nodes will modify the node.
                    add_new_id(node_map, node)
                    # Then add the new node to the destination tree
                    entry_links_node.append(new_node)

            update_all_node_ids(destination_tree.iter(), node_map)
            destination_tree.write(file_path)


if __name__ == '__main__':
    copy_changes_from_template(overwrite=False)
