import os
from typing import TYPE_CHECKING
from xml.etree import ElementTree as ET

from util.node_util import NodeUtil

if TYPE_CHECKING:
    from system.system import System


class SystemFile:
    nodes_by_type: dict[str, NodeUtil] = {}
    nodes_by_id: dict[str, NodeUtil] = {}
    nodes_by_name: dict[str, list[NodeUtil]] = {}

    def __init__(self, system: 'System', path):
        self.system = system  # Link to parent
        self.name = os.path.split(path)[1]
        print(f"Initializing {self.name}")
        set_namespace_from_file(path)
        self.source_tree = ET.parse(path)
        self.nodes_by_id = {}
        for element in self.source_tree.findall('.//*[@id]'):
            node = NodeUtil(self, element)
            self.nodes_by_id.update({node.id: node})


def set_namespace_from_file(filename):
    extension = os.path.splitext(filename)[1]
    if extension == ".cat":
        ET.register_namespace("", "http://www.battlescribe.net/schema/catalogueSchema")
    elif extension == ".gst":
        ET.register_namespace("", "http://www.battlescribe.net/schema/gameSystemSchema")
