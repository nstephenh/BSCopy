# importing the module
import ast
import json
import os

from text_to_rules import text_to_rules
from util import pydict
from util.system_util import read_system, files_in_system, get_root_rules_node, save_system

game_system_location = os.path.expanduser('~/BattleScribe/data/moreus-heresy/')

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
        print(page_number)
        if 'additions' in page.keys():
            print("\tProcessing additions")
            for addition in page['additions']:
                if addition['type'] == "Special Rules":
                    # As of now this assumes format=block
                    expected_ids = addition['associated_nodes']

                    text_block = addition['content']
                    rules_ids = text_to_rules(root_rules_node, text_block, page_number, pub_id)
                    addition['associated_nodes'] = rules_ids
                    # Check if an existing ID is not found / created.
                    for rule_id in expected_ids:
                        if rule_id not in rules_ids:
                            pass
                            # TODO:  If not, delete it.

    save_system()  # Save updates to system file

    # If we make any changes to data, we can write them back to the file
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(pydict.dump_dict(d))
