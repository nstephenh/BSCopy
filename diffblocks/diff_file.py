import difflib
from typing import TYPE_CHECKING

from diffblocks.diffblock import DiffLine, DiffBlock

if TYPE_CHECKING:
    from diffblocks.system_diff import SystemDiff


class DiffFile:
    def __init__(self, system_diff: 'SystemDiff', diff_item):
        self.name = diff_item.a_path
        self.system_diff = system_diff

        self.system_file_left = None
        for file in system_diff.system_left.files:
            if file.name == diff_item.a_path:
                self.system_file_left = file
                break
        if self.system_file_left is None:
            print(f"Could not find file for {diff_item.a_path} in base")

        self.system_file_right = None
        for file in system_diff.system_right.files:
            if file.name == diff_item.b_path:
                self.system_file_right = file
                break
        if self.system_file_right is None:
            print(f"Could not find file for {diff_item.b_path} in branch")

        self.blocks: {int: DiffBlock} = {}

        a_file = diff_item.a_blob.data_stream.read().decode('utf-8')
        b_file = diff_item.b_blob.data_stream.read().decode('utf-8')
        diff_lib = difflib.Differ()
        debug = False
        a_count = 0
        b_count = 0
        block_counter = 0
        last_line_is_left = False
        justify = 16
        for line in diff_lib.compare(a_file.splitlines(), b_file.splitlines()):
            line = line.rstrip()
            if line.startswith('  ') or line == " " or line == "":
                a_count += 1
                b_count += 1
                if block_counter in self.blocks.keys():  # End the block
                    block_counter += 1
                last_line_is_left = False
                if debug:
                    print(f"l {a_count} | r {b_count}".ljust(justify) + line)
            elif line.startswith(DiffLine.REMOVE):
                a_count += 1
                diff_line = DiffLine(a_count, DiffLine.REMOVE, line[2:], self.system_file_left)
                if block_counter not in self.blocks.keys():
                    self.blocks[block_counter] = DiffBlock()
                self.blocks[block_counter].add_line(diff_line)
                last_line_is_left = True
                if debug:
                    print(f"l {a_count}".ljust(justify) + line)
            elif line.startswith(DiffLine.ADD):
                b_count += 1
                diff_line = DiffLine(b_count, DiffLine.ADD, line[2:], self.system_file_right)
                if block_counter not in self.blocks.keys():
                    self.blocks[block_counter] = DiffBlock()
                self.blocks[block_counter].add_line(diff_line)
                last_line_is_left = False
                if debug:
                    print(f"r {b_count}".ljust(justify) + line)
            elif line.startswith(DiffLine.NOTE):  # Line is annotation of the above line.
                if last_line_is_left:
                    diff_line = DiffLine(a_count, DiffLine.NOTE, line[2:])
                else:
                    diff_line = DiffLine(b_count, DiffLine.NOTE, line[2:])
                self.blocks[block_counter].add_line(diff_line, note_is_left=last_line_is_left)

    def get_pretty_diff(self):
        output_lines = [f"## {self.name}"]
        if self.system_file_left is None:
            output_lines.append("File was added")
        elif self.system_file_right is None:
            output_lines.append("File was removed")
        else:
            for block in self.blocks.values():
                output_lines.append(block.get_pretty_diff())
        output_lines.append("")
        return "\n".join(output_lines)
