# importing the module
import ast
import json
import os

from text_to_rules import text_to_rules
from util import pydict
from util.log_util import print_styled, STYLES, get_diff
from util.system_util import read_system, files_in_system, get_root_rules_node, save_system, rules_list, \
    get_node_from_system
from util.node_util import get_description
from util.text_utils import column_text_to_paragraph_text

game_system_location = os.path.expanduser('~/BattleScribe/data/moreus-heresy/')


def get_associated_nodes():
    expected_ids = []
    if hasattr(change, 'associated_nodes'):
        expected_ids = change['associated_nodes']
    return expected_ids


if __name__ == '__main__':
    read_system()

    # Hardcoded for now, but eventually loop over every .pydict file
    file_path = os.path.join(game_system_location, 'panoptica.pydict')
    with open(file_path, encoding='utf-8') as f:
        data = f.read()

    # TODO: determine what rules node an errata may apply to.
    file_to_save_to = ".gst"
    tree_to_update = ""
    for filepath in files_in_system.keys():
        if file_to_save_to in filepath:
            tree_to_update = files_in_system[filepath]
            break
    if tree_to_update == "":
        print("No file to update found!")
    root_rules_node = get_root_rules_node(tree_to_update)

    # reconstructing the data as a dictionary
    d = ast.literal_eval(data)
    document = d['document']
    pub_id = document["bsPubID"]
    for page in document["pages"]:
        page_number = page['pageNumber']
        print(f"Page: {page_number}")
        if 'additions' in page.keys():
            print("\tProcessing additions")
            for addition in page['additions']:
                if addition['type'] == "Special Rules":
                    # As of now this assumes format=block
                    expected_ids = get_associated_nodes()

                    text_block = addition['content']
                    rules_ids = text_to_rules(root_rules_node, text_block, page_number, pub_id)
                    addition['associated_nodes'] = rules_ids
                    # Check if an existing ID is not found / created.
                    for rule_id in expected_ids:
                        if rule_id not in rules_ids:
                            pass
                            # TODO:  If not, delete it.
        if 'changes' in page.keys():
            print("\tProcessing changes")
            for change in page['changes']:
                if change['type'] == "Special Rule":
                    # As of now this assumes format=block
                    expected_ids = get_associated_nodes()

                    target = change['target_name']
                    print(f"\tErrata for {target}")
                    text_block = change['text']
                    new_text = column_text_to_paragraph_text(text_block)

                    target_paragraph = None
                    if 'paragraph' in change.keys():
                        target_paragraph = change['paragraph']
                        print(f"\tAdd the following to paragraph {target}: {new_text}")

                    node_to_errata = None
                    if target in rules_list.keys():
                        print(f"\tRule exists in data files: {rules_list[target]}")
                        node_to_errata = get_node_from_system(rules_list[target])

                    description = get_description(node_to_errata)
                    existing_text = description.text
                    original_text = description.text  # Backup for diff

                    if new_text in existing_text:
                        print("\tErrata appears already applied.")
                    else:
                        if target_paragraph is not None:
                            update_success = False
                            i = 1
                            replacement_text = ""
                            for paragraph in existing_text.split("\n"):
                                if i == target_paragraph:
                                    update_success = True
                                    replacement_text += paragraph + " " + new_text + "\n"
                                else:
                                    replacement_text += paragraph + "\n"
                                i += 1
                            if update_success:
                                description.text = replacement_text
                                print_styled("\tApplied change", STYLES.PURPLE)
                                diff = get_diff(original_text, description.text, 2)
                                print(diff)
                    change['associated_nodes'] = [rules_list[target]]
                    # Check if an existing ID is not found / created.
                    for rule_id in expected_ids:
                        if rule_id is not rules_list[target]:
                            pass
                            # TODO:  If not, delete it.

    save_system()  # Save updates to system file

    # If we make any changes to data, we can write them back to the file
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(pydict.dump_dict(d))
