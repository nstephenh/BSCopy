import os
import re
from xml.etree import ElementTree as ET

import util.system_globals
from settings import default_system, default_data_directory
from system.system_file import set_namespace_from_file, read_categories
from util.log_util import style_text, STYLES
from util.system_globals import files_in_system, system
from util.text_utils import cleanup_disallowed_bs_characters
from util.generate_util import SHARED_RULES_TYPE, cleanup_file_match_bs_whitespace, BS_NAMESPACES


def read_system(system_name=default_system):
    game_system_location = os.path.join(default_data_directory, system_name)
    game_files = os.listdir(game_system_location)
    for file_name in game_files:
        filepath = os.path.join(game_system_location, file_name)
        if os.path.isdir(filepath) or os.path.splitext(file_name)[1] not in ['.cat', '.gst']:
            continue  # Skip this iteration

        set_namespace_from_file(file_name)
        source_tree = ET.parse(filepath)

        files_in_system[filepath] = source_tree
        read_rules_from_system(source_tree)
        read_wargear_from_system(source_tree)
        read_categories_from_system(source_tree)


def get_root_rules_node(source_tree):
    rules_node = source_tree.find(SHARED_RULES_TYPE)
    if rules_node:
        return
    rules_node = source_tree.find("{http://www.battlescribe.net/schema/gameSystemSchema}sharedRules")
    return rules_node


def read_rules_from_system(source_tree):
    """
    Shared and non-shared rules.
    :param source_tree:
    :return:
    """
    for name, node in all_nodes_for_tree(source_tree, 'rule').items():  # Attempt to find all rules in tree
        util.system_globals.rules_list[name] = node.get('id')


def read_wargear_from_system(source_tree):
    """
    Currently only shared selection entries.
    :param source_tree:
    :return:
    """
    sse_node = source_tree.find("{http://www.battlescribe.net/schema/catalogueSchema}sharedSelectionEntries")
    if not sse_node:
        sse_node = source_tree.find("{http://www.battlescribe.net/schema/gameSystemSchema}sharedSelectionEntries")
        if not sse_node:
            return
    for node in sse_node:
        name = node.get('name')
        id = node.get('id')
        util.system_globals.wargear_list[name] = id



def read_categories_from_system(source_tree):
    util.system_globals.category_list = read_categories(source_tree)


def all_nodes_for_tree(source_tree: ET.ElementTree, tag=''):
    nodes: dict[str, ET.Element] = {}
    for namespace in BS_NAMESPACES:
        for node in source_tree.iter(f"{namespace}{tag}"):  # Attempt to find all rules in tree
            name = cleanup_disallowed_bs_characters(node.get('name'))
            nodes[name] = node
    return nodes


def get_node_from_system(node_id):
    for source_tree in files_in_system.values():
        node = source_tree.find(f".//*[@id='{node_id}']")
        if node:
            return node


def update_links(old_node_id, new_node_id):
    for source_tree in files_in_system.values():
        for node in source_tree.iter(f".//*[@target_id='{old_node_id}']"):
            node.attrib['target_id'] = new_node_id


def remove_node(node_id):
    print(style_text("UNTESTED",
                     [STYLES.BOLD, STYLES.RED]))
    for source_tree in files_in_system.values():
        parent_node = source_tree.find(f".//..[@id='{node_id}']")
        node = parent_node.find(f".//*[@id='{node_id}']")
        if node and parent_node:
            parent_node.remove(node)


def save_system():
    system.save_system()


def find_similar_items(list_to_check: list[str], target, similarity_threshold=0):
    """
    :param list_to_check: list of strings to check
    :param target: string name to look for
    :param similarity_threshold: How many parts from target can be missing
    """
    options = {}
    letters_only = re.compile('[^a-zA-Z]')
    name_components = re.split(r'[ |\-]', target)
    name_components = [letters_only.sub("", x.lower()) for x in name_components]
    for option in list_to_check:
        stripped_option = letters_only.sub("", option.lower())
        likeliness = 0
        for component in name_components:
            # increase the count of that option
            if component in stripped_option:
                likeliness += 1
        if likeliness > 0:
            options[f'"{option}"'] = likeliness
    options = dict(sorted(options.items(), key=lambda item: item[1], reverse=True))
    options = dict(filter(lambda item: item[1] > (len(name_components) - similarity_threshold), options.items()))
    return options
