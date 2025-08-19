from system.system_file import SystemFile


class DiffBlock:

    def __init__(self):
        self.left_lines: ['DiffLine'] = []
        self.right_lines: ['DiffLine'] = []
        self.node = None

    def add_line(self, line: 'DiffLine', note_is_left: bool = False):

        if line.change_type == line.REMOVE:
            self.left_lines.append(line)
        if line.change_type == line.ADD:
            self.right_lines.append(line)
        if line.change_type == line.NOTE:
            if note_is_left:
                self.left_lines.append(line)
            else:
                self.right_lines.append(line)
        if self.node is None:
            self.node = line.node

    def get_type(self):
        if self.left_lines and self.right_lines:
            return "Modify"
        if self.left_lines:
            return "Remove"
        if self.right_lines:
            return "Add"

    def get_pretty_diff(self):
        output_lines = []
        max_line_width = 0
        max_line_number_width = 0
        change_type = self.get_type()
        title = f"### {change_type}"
        if self.node is not None:
            title += f" {self.node}"
        output_lines.append(title)
        output_lines.append("'''xml")

        for line in self.left_lines + self.right_lines:
            if len(line.content) > max_line_width:
                max_line_width = len(line.content)
            if len(str(line.number)) > max_line_number_width:
                max_line_number_width = len(str(line.number))

        for line in self.left_lines + self.right_lines:
            output_lines.append(line.get_pretty_line(max_line_number_width, max_line_width))
        output_lines.append("'''")
        output_lines.append("")
        return "\n".join(output_lines)


class DiffLine:
    ADD = "+ "
    REMOVE = "- "
    NOTE = "? "

    def __init__(self, line_number, change_type: ADD or REMOVE or NOTE, line_content, file: 'SystemFile' = None):
        self.change_type = change_type
        self.number = line_number
        self.content = line_content
        self.node = None

        # See if we can find a node for this line
        if file is None:
            return
        node_candidates = file.all_nodes.filter(lambda x: x.start_line_number == line_number)
        if len(node_candidates) == 1:
            self.node = node_candidates[0]

    def get_pretty_line(self, number_justification, line_justification):
        info_str = f"{self.change_type} {str(self.number).rjust(number_justification)} {self.content.ljust(line_justification)}"
        if self.node is not None:
            info_str += f" |  {str(self.node)}"
        return info_str
