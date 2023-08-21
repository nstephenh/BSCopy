import os
import xml.etree.ElementTree as ET

from util import get_random_bs_id, SHARED_RULES_TYPE

page_number = "96"
publication_id = "89c5-118c-61fb-e6d8"
raw_text = """
Three Word Name 12-96“ 7 5 Heavy 5, Barrage, Blast (3”), Pinning, Rending (5+)
shortname - +3 - Melee, Overload (6+), Sudden Strike (3)
"""

output_file = "weapon_output.xml"
final_output = ""


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


def get_name(component_list):
    # if len(component_list) == 1:
    #     return component_list[0]
    return " ".join(component_list)


def format_quote_alikes(in_str):
    '''
    Converts double quote and it's right and left variations to &quot
    :param in_str:
    :return:
    '''
    return in_str.replace('"', '&quot;').replace('”', '&quot;').replace('“', '&quot;')


rules_list = read_rules_from_system()


def get_generic_rule_name(rule_name):
    # Special handling for some rules:
    if rule_name.startswith('Blast (') or rule_name.startswith('Large Blast ('):
        return "Blast"
    if rule_name == "Twin-Linked":
        return "Twin-linked"
    if rule_name == "Two-Handed":
        return "Two-handed"
    if '(' in rule_name:
        return rule_name.split('(')[0] + '(X)'
    return rule_name


hasError = False
for line in raw_text.split("\n"):
    line = line.strip()
    if line == "":
        continue
    first_half = line.split(",")[0].split(" ")
    type_or_num = first_half[-1]
    try:
        num = int(type_or_num)  # Type is not melee
        offset = 0
        weapon_type = first_half[-2] + ' ' + first_half[-1]
        ap = first_half[-3]
        str = first_half[-4]
        range = first_half[-5]
        weapon_name = get_name(first_half[:-5])
    except Exception:
        # Type is melee
        weapon_type = first_half[-1]
        ap = first_half[-2]
        str = first_half[-3]
        range = first_half[-4]
        weapon_name = get_name(first_half[:-4])

    type_and_srs = line[line.index(weapon_type):]
    range = format_quote_alikes(range)

    print(line)
    print("\t", "w: {} r: {} s: {} ap: {} type: {}".format(
        weapon_name, range, str, ap, weapon_type
    ))
    weapon_rules = type_and_srs.split(',')[1:]
    rules_output = ""
    if weapon_rules:
        rules_output = "<infoLinks>\n"
        for rule_name in weapon_rules:
            rule_name = format_quote_alikes(rule_name.strip())
            rule_full_name = rule_name
            rule_name = get_generic_rule_name(rule_name)
            if rule_name in rules_list:
                rule_id = rules_list[rule_name]
                infolink = f'''infoLink name="{rule_name}" hidden="false" type="rule" id="{get_random_bs_id()}" targetId="{rule_id}"'''
            else:
                print(f"Could not find rule: {rule_name}")
                hasError = True
                continue
            if rule_full_name != rule_name:
                rules_output += f"""\t\t\t<{infolink}>
                <modifiers>
                    <modifier type="set" value="{rule_full_name}" field="name"/>
                </modifiers>
            </infoLink>\n"""
            else:
                rules_output += f"<{infolink}/>\n"
        rules_output += "\t\t</infoLinks>"

    root_id = get_random_bs_id()
    output = f""" <selectionEntry type="upgrade" import="true" name="{weapon_name}" hidden="false" id="{get_random_bs_id()}" publicationId="{publication_id}" page="{page_number}">
        <profiles>
        <profile name="{weapon_name}" typeId="1a1a-e592-2849-a5c0" typeName="Weapon" hidden="false" id="{get_random_bs_id()}" publicationId="{publication_id}" page="{page_number}">
          <characteristics>
            <characteristic name="Range" typeId="95ba-cda7-b831-6066">{range}</characteristic>
            <characteristic name="Strength" typeId="24d9-b8e1-a355-2458">{str}</characteristic>
            <characteristic name="AP" typeId="f7a6-e0d8-7973-cd8d">{ap}</characteristic>
            <characteristic name="Type" typeId="2f86-c8b4-b3b4-3ff9">{type_and_srs}</characteristic>
          </characteristics>
        </profile>
        </profiles>
        {rules_output}
    </selectionEntry>"""
    final_output += "\n" + output

if (hasError):
    print("There were one or more errors, please validate the above")
f = open(output_file, "a")
f.write(final_output)
f.close()
