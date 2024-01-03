#
# In order to make a merge go more smoothly, given two repos, one that mirrors another,
# ensure the revision numbers are the same. This allows a git merge to run more smoothly.
import os.path
import xml.etree.ElementTree as ET

from util import cleanup_file_match_bs_whitespace

bsdata_source = os.path.expanduser('~/BattleScribe/data/')
upstream_game = "horus-heresy"
downstream_game = "moreus-heresy"

upstream_dir = os.path.join(bsdata_source, upstream_game)
downstream_dir = os.path.join(bsdata_source, downstream_game)

ET.register_namespace("", "http://www.battlescribe.net/schema/catalogueSchema")

revision_map = {}  # Filename; revision
# First iterate through the upstream directory and get the revision number of each file
print("Getting revision numbers from upstream")

for file_name in os.listdir(upstream_dir):
    if os.path.splitext(file_name)[1] not in [".cat", ".gst"]:
        continue
    tree = ET.parse(os.path.join(upstream_dir, file_name))
    revision_map[file_name] = tree.getroot().attrib['revision']

print("Updating revision numbers on downstream")
for file_name in os.listdir(downstream_dir):
    if file_name not in revision_map.keys():
        continue
    file_to_update = os.path.join(downstream_dir, file_name)
    tree = ET.parse(file_to_update)
    tree.getroot().attrib['revision'] = revision_map[file_name]
    tree.write(file_to_update, encoding="utf-8")  # utf-8 to keep special characters un-escaped.
    cleanup_file_match_bs_whitespace(file_to_update)

print("Done")
