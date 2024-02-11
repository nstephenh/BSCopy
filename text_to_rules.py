from util.element_util import get_description, update_page_and_pub
from util.log_util import STYLES, print_styled, get_diff
from util.text_utils import bullet_options

page_number = "165"
publication_id = "d9b2-e711-f717-0c45"
first_paragraph_is_flavor = True  # If true, skip the first block of text that ends in ".\n"

file_to_save_to = ".gst"  # first file with this in its name.

raw_text = """
Rule Name
Paragraph of flavor text ending in a period 
or an ellipsis "…"
The actual rules text. 
Will add a newline if an input line ends in a period.
    """


def text_to_rules_dict(text, first_p_is_flavor=False, no_flavor_if_colon=False):
    special_rule_length_threshold = 30

    new_rules = {}
    current_rule = ""
    paragraph_count = 0
    in_paragraph = False
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        if line.isdigit():
            # Probably a page number
            continue
        if len(line) < special_rule_length_threshold and not (line.endswith('.')
                                                              or line.endswith("…")
                                                              or line[0].islower()
                                                              or in_paragraph
                                                              or line[0] in bullet_options):
            # print(f"{line} is likely a special rule")
            current_rule = line
            paragraph_count = 0 if first_p_is_flavor else 1
            if first_p_is_flavor and no_flavor_if_colon and current_rule.endswith(":"):
                paragraph_count = 1
            if current_rule.endswith(":"):
                current_rule = current_rule[:-1]  # Strip colon from name

            new_rules[current_rule] = ""
            continue

        # We now know we are inside a rule.
        if not current_rule:
            print_styled(f"'{line}' does not appear to be part of a rule", STYLES.RED)
            continue

        # Skip this line if it's flavor text.
        # print(f"{line} is part of {current_rule}, paragraph {paragraph_count}")
        if paragraph_count >= 1:
            if current_rule not in new_rules:
                print(new_rules)
                exit()
            new_rules[current_rule] += line

        if line[-1] in [".", "…", ":"]:
            if paragraph_count > 0:
                # add linebreaks between paragraphs:
                new_rules[current_rule] += "\n"
            paragraph_count += 1
            in_paragraph = False  # Reset in paragraph
        else:
            in_paragraph = True
            new_rules[current_rule] += " "  # Space instead of a line break.
    return {name: rule.strip() for name, rule in new_rules.items() if rule.strip()}


def text_to_rules(new_rules_dict, rules_node, page, pub_id):
    """
    Do not use at this time from a library context.
    :param new_rules_dict:
    :param rules_node:
    :param page:
    :param pub_id:
    :return:
    """
    from util.text_gen_utils import create_rule_node

    rules_ids = []
    for rule, rule_text in new_rules_dict.items():
        print(f'\033[1m {rule}\033[0m')
        if rule_text.strip() == "":
            print(f"Rule {rule} could not be read properly")
            continue

        if rule in rules_list.keys():
            print(f"\tRule exists in data files: {rules_list[rule]}")
            node = get_node_from_system(rules_list[rule])
            description = get_description(node)
            diff = get_diff(description.text, rule_text, 2)
            if diff:
                print_styled("\tText Differs!", STYLES.PURPLE)
                print(diff)
                description.text = rule_text
            update_page_and_pub(node, page, publication_id)
            rules_ids.append(rules_list[rule])
        else:
            print_styled("\tNew Rule!", STYLES.GREEN)
            new_node = create_rule_node(rules_node, rule, rule_text, pub_id, page)
            print(rule_text)
            rules_ids.append(new_node.attrib['id'])
    return rules_ids


if __name__ == '__main__':
    # Only import these if being called directly
    from util.system_globals import rules_list, files_in_system
    from util.system_util import get_node_from_system, read_system, save_system, get_root_rules_node

    read_system()
    tree_to_update = ""
    for filepath in files_in_system.keys():
        if file_to_save_to in filepath:
            tree_to_update = files_in_system[filepath]
            break
    if tree_to_update == "":
        print("No file to update found!")
    root_rules_node = get_root_rules_node(tree_to_update)

    rules_dict = text_to_rules_dict(raw_text, first_p_is_flavor=first_paragraph_is_flavor)

    text_to_rules(rules_dict, root_rules_node, page_number, publication_id)

    if len(errors) > 1:
        print("There were one or more errors, please validate the output")
        print(errors)

    save_system()
