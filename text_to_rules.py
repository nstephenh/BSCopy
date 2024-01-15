from util.log_util import STYLES, print_styled, get_diff
from util.node_util import get_description
from util.text_gen_utils import errors, create_rule_node
from util.system_util import rules_list, get_node_from_system, read_system, save_system, get_root_rules_node, \
    files_in_system

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


def text_to_rules(rules_node, text, page, pub_id):
    new_rules = {}
    current_rule = ""
    paragraph_count = 0
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        if len(line) < 50 and not (line.endswith('.') or line.endswith("…")):
            print(f"{line} is likely a special rule")
            current_rule = line
            new_rules[current_rule] = ""
            paragraph_count = 0 if first_paragraph_is_flavor else 1

        # We now know we are inside a rule.

        # Skip this line if it's flavor text.
        print(f"{line} is part of {current_rule}, paragraph {paragraph_count}")
        if paragraph_count >= 1:
            new_rules[current_rule] += line.strip()

        if line[-1] in [".", "…"]:
            if paragraph_count > 0:
                # add linebreaks between paragraphs:
                new_rules[current_rule] += "\n"
            paragraph_count += 1
        else:
            if new_rules[current_rule]:
                new_rules[current_rule] += " "  # Space instead of a line break.
    for rule, rule_text in new_rules.items():
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
            if 'page' not in node.attrib or node.attrib['page'] != page:
                print_styled("\tUpdated page number")
                node.attrib['page'] = page
            if 'publicationId' not in node.attrib or node.attrib['publicationId'] != publication_id:
                print_styled("\tUpdated publication ID")
                node.attrib['publicationId'] = publication_id
        else:
            print_styled("\tNew Rule!", STYLES.GREEN)
            create_rule_node(rules_node, rule, rule_text, pub_id, page)
            print(rule_text)


if __name__ == '__main__':
    read_system()
    tree_to_update = ""
    for filepath in files_in_system.keys():
        if file_to_save_to in filepath:
            tree_to_update = files_in_system[filepath]
            break
    if tree_to_update == "":
        print("No file to update found!")
    root_rules_node = get_root_rules_node(tree_to_update)

    text_to_rules(root_rules_node, raw_text, page_number, publication_id)

    if len(errors) > 1:
        print("There were one or more errors, please validate the output")
        print(errors)

    save_system()
