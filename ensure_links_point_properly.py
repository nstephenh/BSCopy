#
# In order to make a merge go more smoothly, given two repos, one that mirrors another,
# ensure the revision numbers are the same. This allows a git merge to run more smoothly.
import os.path
import re
import xml.etree.ElementTree as ET

from util import cleanup_file_match_bs_whitespace

bsdata_source = os.path.expanduser('~/BattleScribe/data/')
upstream_game = "horus-heresy"
downstream_game = "moreus-heresy"

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
