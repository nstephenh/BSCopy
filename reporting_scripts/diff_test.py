import argparse
import datetime
import os
import sys

from git import Repo  # pip install -r GitPython

# Force python XML parser not faster C accelerators
# because we can't hook the C implementation
sys.modules['_elementtree'] = None
print(os.getcwd())
sys.path.insert(1, os.getcwd() + "/BSCopy")

from diffblocks.system_diff import SystemDiff
from settings import default_data_directory

from system.constants import SystemSettingsKeys, GameImportSpecs
from system.system import System

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument("-merge_base")
    args = parser.parse_args()

    merge_base = args.merge_base

    if args.merge_base is None:  # for testing
        merge_base = "1930446af7fd78679d559fb80ffeff5c2bb13b46"

    system_name = 'horus-heresy-3rd-edition'

    repo = Repo(os.path.join(default_data_directory, 'horus-heresy-3rd-edition'))
    original_head = None
    try:
        original_head = repo.head.ref
        print(f"Current head: {original_head}")
    except Exception as e:
        pass  # This doesn't work with a detached head, so don't worry about it.
    head_commit = list(repo.iter_commits())[0]
    main_commit = None
    for commit in repo.iter_commits():
        if commit.hexsha == merge_base:
            main_commit = commit
            break
    print(main_commit)
    if main_commit is None:
        print(f"Could not find merge base commit {merge_base}")
        exit(1)

    system_right = System(system_name,
                          settings={
                              SystemSettingsKeys.GAME_IMPORT_SPEC: GameImportSpecs.HERESY3E,
                              "diff": True
                          },
                          )

    # Now, check out the status on main so we can get information about those lines.
    print(f"Checking out system at commit {merge_base}:")
    repo.git.checkout(main_commit)
    system_left = System(system_name,
                         settings={
                             SystemSettingsKeys.GAME_IMPORT_SPEC: GameImportSpecs.HERESY3E,
                             "diff": True
                         },
                         )

    diff_index = main_commit.diff(head_commit)

    system_diff = SystemDiff(system_left, system_right, diff_index)

    # Finally, composite all the lines into readable results.
    output = f"As of {head_commit} at {datetime.datetime.now()}\n" + system_diff.get_pretty_diff()
    if len(output) > 65536:
        lines = output.count("\n")
        truncated = output[:65400]
        truncated_lines = truncated.count("\n")
        truncated = f"Truncated due to length: {lines - truncated_lines} lines dropped\n" \
                    + truncated + "\n```\nOriginal in test output"
        print(output)
        output = truncated
    with open("diff_result.txt", mode='w') as file:
        file.write(output)
        print(f"Output written to {file.name}")
    if original_head:
        # Restore checkout to normal (for local testing)
        print(f"Restoring checkout to {original_head}")
        repo.git.checkout(original_head)
