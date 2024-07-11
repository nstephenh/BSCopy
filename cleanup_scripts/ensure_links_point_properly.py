#
# If you've forked a repo, then you need to change the IDs for the gst and each cat file.
# This script can be run to notify you if any of the cat files ID's need to be changed
# and updates any catalogue links referencing the old IDs.
#
import os.path
import re
import xml.etree.ElementTree as ET

from util.generate_util import get_random_bs_id

if __name__ == '__main__':
    pass  # Putting this up here will cause the rest of the script to run without indenting it.

bsdata_source = os.path.expanduser('~/BattleScribe/data/')
upstream_game = "horus-heresy"
downstream_game = "moreus-heresy"

change_ids = True  # If a root ID is the same, should we change it?
change_full_id = False  # If False, will only update the last digit of the ID.

upstream_dir = os.path.join(bsdata_source, upstream_game)
downstream_dir = os.path.join(bsdata_source, downstream_game)

original_id_map = {}  # Filename: original_id
new_id_map = {}  # Filename: new_id
# First iterate through the upstream directory and get the revision number of each file
print("Getting IDs from upstream")

for file_name in os.listdir(upstream_dir):
    if os.path.splitext(file_name)[1] not in [".cat", ".gst"]:
        continue
    tree = ET.parse(os.path.join(upstream_dir, file_name))
    if os.path.splitext(file_name)[1] == ".gst":
        file_name = "GST"  # Since the GST name may have changed, just store it as "GST"
    original_id_map[file_name] = tree.getroot().attrib['id']

print("Getting new IDs from downstream")
for file_name in os.listdir(downstream_dir):
    file = os.path.join(downstream_dir, file_name)
    if os.path.splitext(file_name)[1] == ".gst":
        file_name = "GST"  # Since the GST name may have changed, get from the "GST" node in the map.
    if file_name not in original_id_map.keys():
        continue
    tree = ET.parse(file)
    new_id_map[file_name] = tree.getroot().attrib['id']
    if original_id_map[file_name] == new_id_map[file_name] and change_ids:
        if change_full_id:
            new_id = get_random_bs_id()
        else:
            old_last_digit = new_id_map[file_name][-1]
            new_last_digit = hex(int(old_last_digit, 16) + 1)[-1]
            new_id = new_id_map[file_name][:-1] + new_last_digit

        print(f"\tFile {file_name} should get a new id")
        print(f"\t\tOld ID: {original_id_map[file_name]}, New ID: {new_id}")
        tree.getroot().attrib['id'] = new_id
        new_id_map[file_name] = new_id

if not change_ids:
    keys_to_pop = []
    for key in original_id_map.keys():
        if original_id_map[key] == new_id_map[key]:
            print(f"\tKey {key} needs to be changed")
            keys_to_pop.append(key)

    for key in keys_to_pop:
        original_id_map.pop(key)  # prevent errors printing about this key

print("Looking for occurrences of old IDs")
for file_name in os.listdir(downstream_dir):
    if os.path.splitext(file_name)[1] not in [".cat", ".gst"]:
        continue
    file_to_update = os.path.join(downstream_dir, file_name)
    with open(file_to_update, 'r', encoding="utf-8") as f:
        content = f.read()
    for referenced_file_name, old_id in original_id_map.items():
        new_id = new_id_map[referenced_file_name]


        def substitute_and_print(_):
            print(f"\tInstance of {referenced_file_name}'s ID found in {file_name}")
            return new_id


        content = re.sub(old_id, substitute_and_print, content)
    with open(file_to_update, 'w', encoding="utf-8") as f:
        f.write(content)

print("Done")
