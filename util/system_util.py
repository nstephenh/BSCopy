import os
import re
from xml.etree import ElementTree as ET

from util.log_util import style_text, STYLES
from util.text_utils import cleanup_disallowed_bs_characters
from util.generate_util import SHARED_RULES_TYPE, cleanup_file_match_bs_whitespace, BS_NAMESPACES

files_in_system: dict[str, ET.ElementTree] = {}

rules_list: dict[str, str] = {}
wargear_list: dict[str, str] = {}
category_list: dict[str, str] = {}


def set_namespace_for_file(filename):
    extension = os.path.splitext(filename)[1]
    if extension == ".cat":
        ET.register_namespace("", "http://www.battlescribe.net/schema/catalogueSchema")
    elif extension == ".gst":
        ET.register_namespace("", "http://www.battlescribe.net/schema/gameSystemSchema")


def read_system():
    game_system_location = os.path.expanduser('~/BattleScribe/data/moreus-heresy/')
    game_files = os.listdir(game_system_location)
    for file_name in game_files:
        filepath = os.path.join(game_system_location, file_name)
        if os.path.isdir(filepath) or os.path.splitext(file_name)[1] not in ['.cat', '.gst']:
            continue  # Skip this iteration

        set_namespace_for_file(file_name)
        source_tree = ET.parse(os.path.join(filepath))

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
    global rules_list
    for namespace in BS_NAMESPACES:
        for node in source_tree.iter(f"{namespace}rule"):  # Attempt to find all rules in tree
            name = cleanup_disallowed_bs_characters(node.get('name'))
            rules_list[name] = node.get('id')


def read_wargear_from_system(source_tree):
    global wargear_list
    sse_node = source_tree.find("{http://www.battlescribe.net/schema/catalogueSchema}sharedSelectionEntries")
    if not sse_node:
        sse_node = source_tree.find("{http://www.battlescribe.net/schema/gameSystemSchema}sharedSelectionEntries")
        if not sse_node:
            return
    for node in sse_node:
        name = node.get('name')
        id = node.get('id')
        wargear_list[name] = id


def read_categories_from_system(source_tree):
    global category_list
    rules_node = source_tree.find("{http://www.battlescribe.net/schema/catalogueSchema}categoryEntries")
    if not rules_node:
        rules_node = source_tree.find("{http://www.battlescribe.net/schema/gameSystemSchema}categoryEntries")
        if not rules_node:
            return
    for node in rules_node:
        name = node.get('name')
        if name.endswith(":"):
            name = name[:-1]
        if name.lower().endswith(" sub-type"):
            name = name[:-len(" sub-type")]
            if name.lower().endswith(" unit"):
                name = name[:-len(" unit")]
        elif name.lower().endswith(" unit-type"):
            name = name[:-len(" unit-type")]
        id = node.get('id')
        category_list[name] = id


def get_node_from_system(node_id):
    for source_tree in files_in_system.values():
        node = source_tree.find(f".//*[@id='{node_id}']")
        if node:
            return node


def remove_node(node_id):
    print(style_text("UNTESTED",
                     [STYLES.BOLD, STYLES.RED]))
    for source_tree in files_in_system.values():
        parent_node = source_tree.find(f".//..[@id='{node_id}']")
        node = parent_node.find(f".//*[@id='{node_id}']")
        if node and parent_node:
            parent_node.remove(node)


def save_system():
    print("Saving system")
    count = len(files_in_system)
    i = 0
    for filepath, source_tree in files_in_system.items():
        i += 1
        print('\r', end="")
        print(f"Saving file ({i}/{count}): {filepath}", end="")
        set_namespace_for_file(filepath)
        source_tree.write(filepath, encoding="utf-8")  # utf-8 to keep special characters un-escaped.
        cleanup_file_match_bs_whitespace(filepath)


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
