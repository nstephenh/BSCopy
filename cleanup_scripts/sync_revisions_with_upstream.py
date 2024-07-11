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
downstream_game = "moreus-heresy"

upstream_dir = os.path.join(bsdata_source, upstream_game)
downstream_dir = os.path.join(bsdata_source, downstream_game)

revision_map: dict[str:int] = {}  # Filename; revision
gsrevision_map: dict[str:int] = {}  # Filename; revision

original_id_map: dict[str:int] = {}  # Filename: original_id

id_translation_table: dict[int:int] = {}  # old_id: new_id

new_files = []

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="Given two systems, ensure revision numbers are in sync ")
    parser.add_argument("--r", '-r', action='store_true',
                        help="Reset downstream with a rebase on upstream")
    parser.add_argument("--skip_map", '-s', action='store_true',
                        help="use a existing id_map.json file, skipping making a new one")
    args = parser.parse_args()

    # First iterate through the upstream directory and get the revision number of each file
    print("Getting revision numbers from upstream")

    old_system = System(upstream_game)
    for system_file in old_system.files:
        file_name = system_file.name
        if system_file.is_gst:
            file_name = "GST"  # Since the GST name may change, just store it as "GST"

        revision_map[file_name] = system_file.revision
        gsrevision_map[file_name] = system_file.game_system_revision
        original_id_map[file_name] = system_file.id

    print("Updating revision numbers on downstream")
    new_system = System(downstream_game)
    for system_file in new_system.files:
        file_name = system_file.name
        if system_file.is_gst:
            file_name = "GST"  # Since the GST name may have changed, get from the "GST" node in the map.
        if file_name not in original_id_map.keys():
            new_files.append(system_file)
            continue

        # update revision and gameSystemRevision
        system_file._source_tree.getroot().attrib['revision'] = revision_map[file_name]
        if file_name != "GST":
            system_file._source_tree.getroot().attrib['gameSystemRevision'] = gsrevision_map[file_name]

        id_translation_table[original_id_map[file_name]] = system_file.id
    new_system.save_system()

    with open(os.path.join(downstream_dir, 'id_map.json'), 'w') as f:
        f.write(json.dumps(id_translation_table))

    print("Done")
