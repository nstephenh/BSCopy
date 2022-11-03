import copy
import os
import xml.etree.ElementTree as ET

from util import find_comment_value, ENTRY_LINK_TYPE, update_all_node_ids, add_new_id, get_mod_and_con_ids, \
    MODIFIER_TYPE, CONDITION_GROUP_TYPE, CONDITION_TYPE, COMMENT_NODE_TYPE

if __name__ == '__main__':

    list_legion_additions = False
    ET.register_namespace("", "http://www.battlescribe.net/schema/catalogueSchema")

    source_tree = ET.parse(os.path.expanduser('~/BattleScribe/data/horus-heresy/2022 - LA Template.cattemplate'))

    base_path = os.path.expanduser('~/BattleScribe/data/horus-heresy')
    la_files = os.listdir(base_path)

    for file_name in la_files:
        if file_name.startswith("2022 - LA - "):
            file_path = os.path.join(base_path, file_name)
            destination_tree = ET.parse(file_path)
            node_map = {}
            # generate a node id map of all nodes that already exist in the destination tree
            for node in destination_tree.iter():
                target_id = node.attrib.get("id")
                if target_id:
                    source_id = find_comment_value(node)
                    if source_id:
                        node_map[source_id] = target_id

            backup_tree = copy.deepcopy(destination_tree)
            # Check existing entries, and print potential changes
            for destination_node in backup_tree.findall("./{}s/{}".format(ENTRY_LINK_TYPE, ENTRY_LINK_TYPE)):
                target_id = destination_node.attrib.get("id")
                name = destination_node.attrib.get("name")
                if target_id not in node_map.values():
                    if list_legion_additions:
                        print("{} adds SSEG {}".format(file_name, name))
                else:  # Inspect existing node contents
                    index = list(node_map.values()).index(target_id)
                    bs_id = list(node_map.keys())[index]
                    source_node = source_tree.find("./{}s/{}[@id='{}']".format(ENTRY_LINK_TYPE, ENTRY_LINK_TYPE, bs_id))

                    # List all mods and cons that need to be copied from the source to destination
                    source_mods_and_cons = get_mod_and_con_ids(source_node.iter())
                    destination_m_and_c = get_mod_and_con_ids(destination_node.iter())
                    for node_id in source_mods_and_cons:
                        if node_id not in destination_m_and_c:
                            print("{}'s {} needs updated with {}".format(file_name, name, node_id))

                    # Find all legion specific modifiers and conditions
                    if list_legion_additions:
                        for descendant in source_node.iter():
                            if descendant.tag in [MODIFIER_TYPE, CONDITION_TYPE, CONDITION_GROUP_TYPE]:
                                node_id = find_comment_value(descendant, node_id=True)
                                if node_id is None:
                                    print("{}'s {} adds {}".format(file_name, name, descendant))

            # List SSEGs that need copied to the target
            for destination_node in source_tree.findall("./{}s/{}".format(ENTRY_LINK_TYPE, ENTRY_LINK_TYPE)):
                target_id = destination_node.attrib.get("id")
                name = destination_node.attrib.get("name")
                if target_id not in node_map.keys():
                    print("{} needs SSEG {}(id={}) copied".format(file_name, name, target_id))
