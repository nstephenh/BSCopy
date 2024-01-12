import os
import xml.etree.ElementTree as ET
from xml.etree import ElementTree as ET

from util.text_utils import cleanup_disallowed_bs_characters
from util.generate_util import SHARED_RULES_TYPE

files_in_system = {}  # filename: ET  # Dict of trees accessed this session. If we need to update the trees, save these.

rules_list = {}
wargear_list = {}
category_list = {}


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

        files_in_system[file_name] = source_tree
        read_rules_from_system(source_tree)
        read_wargear_from_system(source_tree)
        read_categories_from_system(source_tree)


def read_rules_from_system(source_tree):
    global rules_list

    rules_node = source_tree.find(SHARED_RULES_TYPE)
    if not rules_node:
        rules_node = source_tree.find("{http://www.battlescribe.net/schema/gameSystemSchema}sharedRules")
        if not rules_node:
            return
    for node in rules_node:
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
