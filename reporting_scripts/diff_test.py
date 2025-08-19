# Force python XML parser not faster C accelerators
# because we can't hook the C implementation
import argparse
import difflib
import os
import sys

from git import Repo

sys.modules['_elementtree'] = None
print(os.getcwd())
sys.path.insert(1, os.getcwd() + "/BSCopy")

from system.constants import SystemSettingsKeys, GameImportSpecs
from system.system import System

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("-merge_base")
    args = parser.parse_args()

    merge_base = args.merge_base

    if args.merge_base is None:  # for testing
        merge_base = "f8adfcf7dc5b689f51c70c6dd99c8c47e22e4704"

    system = System('horus-heresy-3rd-edition',
                    settings={
                        SystemSettingsKeys.GAME_IMPORT_SPEC: GameImportSpecs.HERESY3E,
                        "diff": True
                    },
                    )
    crusade = system.get_node_by_id("8562-592c-8d4b-a1f0")

    print(crusade.start_line_number)
    repo = Repo(system.game_system_location)
    head_commit = list(repo.iter_commits())[0]
    main_commit = None
    for commit in repo.iter_commits():
        if commit.hexsha == merge_base:
            main_commit = commit
            break
    print(main_commit)
    diff_index = main_commit.diff(head_commit)
    output_lines = []
    for diff_item in diff_index:
        print(diff_item.a_path)
        output_lines.apend(f"# {diff_item.a_path}")
        if not (diff_item.a_path.endswith('.cat') or diff_item.a_path.endswith('.gst')):
            continue
        a_file = diff_item.a_blob.data_stream.read().decode('utf-8')
        b_file = diff_item.b_blob.data_stream.read().decode('utf-8')
        diff_lib = difflib.Differ()
        a_count = 0
        b_count = 0
        removed_things = []
        added_or_modified_nodes = []

        system_file = None
        for file in system.files:
            if file.name == diff_item.a_path:
                system_file = file
                break

        if system_file is None:
            output_lines.append(f"Could not find file for {diff_item.a_path}")
            print(f"Could not find file for {diff_item.a_path}")
        last_line_from_a = False
        last_line_from_b = False
        for line in diff_lib.compare(a_file.splitlines(), b_file.splitlines()):
            if line.startswith('  '):
                a_count += 1
                b_count += 1
            elif line.startswith('- '):
                a_count += 1
                print(a_count, line)
                last_line_from_a = True
                last_line_from_b = False
            elif line.startswith('+ '):
                b_count += 1
                last_line_from_a = False
                last_line_from_b = True
                print(b_count, line)
                node_candidates = system_file.all_nodes.filter(lambda x: x.start_line_number == b_count)
                if len(node_candidates) == 1:
                    print(str(node_candidates[0]))
            elif line.startswith('? '):  # Line is annotation of the above line.
                pass
    with open("diff_result.txt", mode='w') as file:
        file.write("\n".join(output_lines))
