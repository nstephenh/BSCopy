from system_constants import name_synonyms
from util.system_util import rules_list, wargear_list
from util.text_utils import get_generic_rule_name, remove_plural
from util.generate_util import get_random_bs_id
import xml.etree.ElementTree as ET

errors = ""


def check_alt_names(name):
    if name in name_synonyms:
        return name_synonyms[name]
    return name


def get_entrylink(name, pts=None, only=False, default=False, max_amount=1):
    global errors
    lookup_name = check_alt_names(name)
    if "Two" in lookup_name:
        lookup_name = lookup_name.split("Two")[1].strip()
        lookup_name = remove_plural(lookup_name)
    if "Mounted" in lookup_name:
        lookup_name = lookup_name.split("Mounted")[1].strip()

    default_amount = ""
    if default:
        default_amount = f'defaultAmount="{max_amount}"'

    if lookup_name not in wargear_list:
        errors = errors + f"Could not find wargear for: {name}\n"
        if lookup_name != name:
            errors = errors + f"\t Checked under {lookup_name} \n"
        return ""

    modifiers = ""
    if lookup_name != name:
        modifiers = f"""
      <modifiers>
        <modifier type="set" value="{lookup_name}" field="name"/>
      </modifiers>
"""
    wargear_id = wargear_list[lookup_name]
    link_text = f'entryLink import="true" name="{lookup_name}" hidden="false" type="selectionEntry" id="{get_random_bs_id()}" targetId="{wargear_id}" {default_amount}'
    if pts is not None:  # if points, this must be a selectable option.
        return f"""
    <{link_text}>
      <constraints>
        <constraint type="max" value="{max_amount}" field="selections" scope="parent" shared="true" id="{get_random_bs_id()}"/>
      </constraints>
      <costs>
        <cost name="Pts" typeId="d2ee-04cb-5f8a-2642" value="{pts}"/>
      </costs>
      {modifiers}
    </entryLink>"""
    elif only:  # If a default option, then set it as min 1 max 1
        return f"""
    <{link_text}>
      <constraints>
        <constraint type="min" value="1" field="selections" scope="parent" shared="true" id="{get_random_bs_id()}"/>
        <constraint type="max" value="1" field="selections" scope="parent" shared="true" id="{get_random_bs_id()}"/>
      </constraints>
    </entryLink>"""
    else:
        return f"\n<{link_text} />"


def rules_list_to_infolinks(rules_for_entry):
    global errors
    rules_output = ""
    if rules_for_entry:
        rules_output = "<infoLinks>\n"
        for rule_name in rules_for_entry:
            rule_name = rule_name.strip()
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
                    errors += f"Could not find rule: {rule_name}\n"
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


def option_group_gen_se(name, pts, default=False, max_amount=1):
    # When an option is a group of options and needs a SE containing multiple entry links.
    sub_options = ""
    and_delims = ["&", "and"]
    default_amount = ""
    if default:
        default_amount = f'defaultAmount="{max_amount}"'
    for and_delim in and_delims:
        if and_delim in name:
            for sub_option in name.split(and_delim):
                sub_options += get_entrylink(sub_option.strip(), only=True)

    return f"""
                      <selectionEntry type="upgrade" name="{name}" hidden="false" id="{get_random_bs_id()}" {default_amount}>
                        <entryLinks>{sub_options}
                        </entryLinks>
                        <constraints>
                        <constraint type="max" value="{max_amount}" field="selections" scope="parent" shared="true" id="{get_random_bs_id()}"/>
                      </constraints>
                      <costs>
                        <cost name="Pts" typeId="d2ee-04cb-5f8a-2642" value="{pts}"/>
                      </costs>
                      </selectionEntry>"""


def create_rule_node(rules_root, name, text, pub, page):
    rule_node = ET.SubElement(rules_root, 'rule', attrib={'name': name, 'hidden': "false",
                                                          'id': get_random_bs_id(), 'page': page,
                                                          'publicationId': pub})
    description_node = ET.SubElement(rule_node, 'description')
    description_node.text = text
    return rule_node

