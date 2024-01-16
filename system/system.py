import os

from system.system_file import SystemFile
from util.node_util import NodeUtil
from settings import default_system, default_data_directory


class System:
    files: [SystemFile] = []
    nodes_by_id: dict[str, NodeUtil] = {}
    nodes_by_name: dict[str, list[NodeUtil]] = {}

    def __init__(self, system_name: str = default_system, data_directory: str = default_data_directory):
        print(f"Initializing {system_name}")

        self.system_name = system_name
        self.game_system_location = os.path.join(default_data_directory, system_name)
        game_files = os.listdir(self.game_system_location)
        for file_name in game_files:
            filepath = os.path.join(self.game_system_location, file_name)
            if os.path.isdir(filepath) or os.path.splitext(file_name)[1] not in ['.cat', '.gst']:
                continue  # Skip this iteration
            self.files.append(SystemFile(self, filepath))
            for file in self.files:
                self.nodes_by_id.update(file.nodes_by_id)
