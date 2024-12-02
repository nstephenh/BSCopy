#
# In order to make a merge go more smoothly, given two repos, one that mirrors another,
# ensure the revision numbers are the same. This allows a git merge to run more smoothly.
import argparse
import json
import os.path
import xml.etree.ElementTree as ET

from system.system import System
from util.generate_util import cleanup_file_match_bs_whitespace
from system.system_file import set_namespace_from_file

bsdata_source = os.path.expanduser('~/BattleScribe/data/')
upstream_game = "horus-heresy"
downstream_game = "horus-heresy-panoptica"

upstream_dir = os.path.join(bsdata_source, upstream_game)
downstream_dir = os.path.join(bsdata_source, downstream_game)

original_id_map: dict[str:int] = {}  # Filename: original_id

id_translation_table: dict[int:int] = {}  # old_id: new_id

new_files = []

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="Given two systems, differentiate their IDs")
    args = parser.parse_args()

    # First iterate through the upstream directory and get the revision number of each file
    print("Getting IDs from upstream")

    old_system = System(upstream_game)
    for system_file in old_system.files:
        file_name = system_file.name
        if system_file.is_gst:
            file_name = "GST"  # Since the GST name may change, just store it as "GST"

        original_id_map[file_name] = system_file.id

    new_system = System(downstream_game)
    for system_file in new_system.files:
        file_name = system_file.name
        if system_file.is_gst:
            file_name = "GST"  # Since the GST name may have changed, get from the "GST" node in the map.
        if file_name not in original_id_map.keys():
            new_files.append(system_file)
            continue
        if system_file.id in original_id_map.values():
            print(f"File ID for {system_file} needs updated")
            last_char = system_file.id[-1]
            incremented = int(last_char, 16) + 1
            last_char = hex(incremented)[-1]  # Only get last character
            new_id = system_file.id[:-1] + last_char
            print("Adjusting all files referencing this")
            for file_to_edit_contents_of in new_system.files:
                with open(file_to_edit_contents_of.path, 'r', encoding="utf-8") as f:
                    filedata = f.read()
                if filedata.count(system_file.id):
                    print(f"\t{file_to_edit_contents_of} contains {filedata.count(system_file.id)} references")
                else:
                    continue
                filedata = filedata.replace(system_file.id, new_id)
                with open(file_to_edit_contents_of.path, 'w', encoding="utf-8") as f:
                    f.write(filedata)


    print("Done")
