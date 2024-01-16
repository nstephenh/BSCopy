import os

from system.system_file import SystemFile
from system.node import Node
from settings import default_system, default_data_directory

IGNORE_FOR_DUPE_CHECK = ['selectionEntryGroup', 'selectionEntry', 'constraint', 'repeat', 'condition',
                         'characteristicType']


class System:

    def __init__(self, system_name: str = default_system, data_directory: str = default_data_directory):
        print(f"Initializing {system_name}")

        self.files: [SystemFile] = []
        self.nodes_by_id: dict[str, Node] = {}
        self.nodes_by_type: dict[str, list[Node]] = {}
        self.nodes_by_name: dict[str, list[Node]] = {}

        self.system_name = system_name
        self.game_system_location = os.path.join(data_directory, system_name)
        game_files = os.listdir(self.game_system_location)
        for file_name in game_files:
            filepath = os.path.join(self.game_system_location, file_name)
            if os.path.isdir(filepath) or os.path.splitext(file_name)[1] not in ['.cat', '.gst']:
                continue  # Skip this iteration
            self.files.append(SystemFile(self, filepath))
        for file in self.files:
            self.nodes_by_id.update(file.nodes_by_id)
            for tag, nodes in file.nodes_by_type.items():
                if tag not in self.nodes_by_type.keys():
                    self.nodes_by_type[tag] = []
                for node in nodes:
                    self.nodes_by_type[tag].append(node)
            for name, nodes in file.nodes_by_name.items():

                if name not in self.nodes_by_name.keys():
                    self.nodes_by_name[name] = []
                self.nodes_by_name[name].extend(nodes)

    def get_duplicates(self) -> dict[str, list['Node']]:

        nodes_with_duplicates = {}
        for name, nodes in self.nodes_by_name.items():
            by_tag = {}
            if len(nodes) > 1:
                for node in nodes:
                    if node.tag not in by_tag.keys():
                        by_tag[node.tag] = []
                    by_tag[node.tag].append(node)
                for tag, tag_nodes in by_tag.items():
                    if tag in IGNORE_FOR_DUPE_CHECK or tag.endswith('Link'):
                        continue
                    if len(tag_nodes) > 1:
                        nodes_with_duplicates[f"{name} - {tag}"] = tag_nodes
        return nodes_with_duplicates
