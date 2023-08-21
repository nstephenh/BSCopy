import os
import xml.etree.ElementTree as ET

from util import SHARED_RULES_TYPE, get_random_bs_id


def rules_list_to_infolinks(rules_for_entry, rules_list):
    global hasError, errors
    rules_output = ""
    if rules_for_entry:
        rules_output = "<infoLinks>\n"
        for rule_name in rules_for_entry:
            rule_name = format_quote_alikes(rule_name.strip())
            rule_full_name = rule_name
            rule_name = get_generic_rule_name(rule_name)
            if rule_name in rules_list:
                rule_id = rules_list[rule_name]
            else:
                rule_name = get_generic_rule_name(rule_name, True)
                if rule_name in rules_list:
                    rule_id = rules_list[rule_name]
                else:
                    print(f"Could not find rule: {rule_name}")
                    hasError = True
                    errors = errors + f"Could not find rule: {rule_name}\n"
                    continue
            infolink = f'''infoLink name="{rule_name}" hidden="false" type="rule" id="{get_random_bs_id()}" targetId="{rule_id}"'''
            if rule_full_name != rule_name:
                rules_output += f"""        <{infolink}>
                <modifiers>
                    <modifier type="set" value="{rule_full_name}" field="name"/>
                </modifiers>
            </infoLink>\n"""
            else:
                rules_output += f"        <{infolink}/>\n"
        rules_output += "      </infoLinks>"
    return rules_output


def get_generic_rule_name(rule_name, after_dash=False):
    # Special handling for some rules:
    if rule_name.startswith('Blast (') or rule_name.startswith('Large Blast (') \
            or rule_name.startswith('Massive Blast ('):
        return "Blast"
    if after_dash and '-' in rule_name:  # for Twin-linked, Two-handed, and Master-crafted
        components = rule_name.split('-')
        return components[0] + "-" + components[1].lower()

    if '(' in rule_name:
        return rule_name.split('(')[0] + '(X)'
    return rule_name


def format_quote_alikes(in_str):
    '''
    Converts double quote and it's right and left variations to &quot
    :param in_str:
    :return:
    '''
    return in_str.replace('"', '&quot;').replace('”', '&quot;').replace('“', '&quot;')


def read_rules_from_system():
    ET.register_namespace("", "http://www.battlescribe.net/schema/catalogueSchema")
    game_system_location = os.path.expanduser('~/BattleScribe/data/panoptica-heresy/')

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
    game_system_location = os.path.expanduser('~/BattleScribe/data/panoptica-heresy/')

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
