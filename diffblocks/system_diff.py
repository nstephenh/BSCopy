from diffblocks.diff_file import DiffFile
from system.system import System


class SystemDiff:
    def __init__(self, system_left: 'System', system_right: 'System', diff_index):
        self.system_left: 'System' = system_left
        self.system_right: 'System' = system_right

        self.files: [DiffFile] = []
        for diff_item in diff_index:
            if not (diff_item.a_path.endswith('.cat') or diff_item.a_path.endswith('.gst')):
                continue
            self.files.append(DiffFile(self, diff_item))

    def get_pretty_diff(self):
        output_lines = []
        for file in self.files:
            output_lines.append(file.get_pretty_diff())
        return "\n".join(output_lines)
