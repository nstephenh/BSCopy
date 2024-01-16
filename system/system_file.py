import os
from typing import TYPE_CHECKING
from xml.etree import ElementTree as ET

from system.node import Node

if TYPE_CHECKING:
    from system.system import System


class SystemFile:

    def __init__(self, system: 'System', path):
        self.system = system  # Link to parent
        self.name = os.path.split(path)[1]
        print(f"Initializing {self.name}")

        self.nodes_by_id: dict[str, Node] = {}
        self.nodes_by_type: dict[str, list[Node]] = {}
        self.nodes_by_name: dict[str, list[Node]] = {}

        self.namespace = set_namespace_from_file(path)
        self.source_tree = ET.parse(path)
        self.nodes_by_id = {}
        for element in self.source_tree.findall('.//*[@id]'):
            node = Node(self, element)
            self.nodes_by_id.update({node.id: node})
            if node.tag not in self.nodes_by_type.keys():
                self.nodes_by_type[node.tag] = []
            self.nodes_by_type[node.tag].append(node)

            if node.name not in self.nodes_by_name.keys():
                self.nodes_by_name[node.name] = []
            self.nodes_by_name[node.name].append(node)


def get_namespace_from_file(filename: str):
    extension = os.path.splitext(filename)[1]
    if extension == ".cat":
        return "http://www.battlescribe.net/schema/catalogueSchema"
    elif extension == ".gst":
        return "http://www.battlescribe.net/schema/gameSystemSchema"


def set_namespace_from_file(filename):
    namespace = get_namespace_from_file(filename)
    ET.register_namespace("", namespace)
    return namespace
