import os
import xml.etree.ElementTree as ET

from util import SHARED_RULES_TYPE



def read_rules_from_system():
    ET.register_namespace("", "http://www.battlescribe.net/schema/catalogueSchema")
    game_system_location = os.path.expanduser('~/BattleScribe/data/moreus-heresy/')

    game_files = os.listdir(game_system_location)
    rules_list = {}

    for file_name in game_files:
        filepath = os.path.join(game_system_location, file_name)
        if os.path.isdir(filepath) or os.path.splitext(file_name)[1] not in ['.cat', '.gst']:
            continue  # Skip this iteration
        source_tree = ET.parse(os.path.join(filepath))
        rules_node = source_tree.find(SHARED_RULES_TYPE)
        if not rules_node:
            rules_node = source_tree.find("{http://www.battlescribe.net/schema/gameSystemSchema}sharedRules")
            if not rules_node:
                continue
        for node in rules_node:
            name = node.get('name')
            id = node.get('id')
            rules_list[name] = id
    return rules_list


def read_wargear_from_system():
    ET.register_namespace("", "http://www.battlescribe.net/schema/catalogueSchema")
    game_system_location = os.path.expanduser('~/BattleScribe/data/moreus-heresy/')

    game_files = os.listdir(game_system_location)
    wargear_list = {}

    for file_name in game_files:
        filepath = os.path.join(game_system_location, file_name)
        if os.path.isdir(filepath) or os.path.splitext(file_name)[1] not in ['.cat', '.gst']:
            continue  # Skip this iteration
        source_tree = ET.parse(os.path.join(filepath))
        sse_node = source_tree.find("{http://www.battlescribe.net/schema/catalogueSchema}sharedSelectionEntries")
        if not sse_node:
            sse_node = source_tree.find("{http://www.battlescribe.net/schema/gameSystemSchema}sharedSelectionEntries")
            if not sse_node:
                continue
        for node in sse_node:
            name = node.get('name')
            id = node.get('id')
            wargear_list[name] = id
    return wargear_list


def read_categories_from_system():
    ET.register_namespace("", "http://www.battlescribe.net/schema/catalogueSchema")
    game_system_location = os.path.expanduser('~/BattleScribe/data/moreus-heresy/')

    game_files = os.listdir(game_system_location)
    category_list = {}

    for file_name in game_files:
        filepath = os.path.join(game_system_location, file_name)
        if os.path.isdir(filepath) or os.path.splitext(file_name)[1] not in ['.cat', '.gst']:
            continue  # Skip this iteration
        source_tree = ET.parse(os.path.join(filepath))
        rules_node = source_tree.find("{http://www.battlescribe.net/schema/catalogueSchema}categoryEntries")
        if not rules_node:
            rules_node = source_tree.find("{http://www.battlescribe.net/schema/gameSystemSchema}categoryEntries")
            if not rules_node:
                continue
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
    return category_list

rules_list = read_rules_from_system()
wargear_list = read_wargear_from_system()
category_list = read_categories_from_system()