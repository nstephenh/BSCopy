import os
from typing import TYPE_CHECKING
from xml.etree import ElementTree as ET

from system.node import Node
from system.node_collection import NodeCollection
from util.generate_util import get_random_bs_id

if TYPE_CHECKING:
    from system.system import System


class SystemFile:

    def __init__(self, system: 'System', path):
        self.system = system  # Link to parent
        self.name = os.path.split(path)[1]
        self.path = path

        self.nodes = NodeCollection([])
        # The goal is to replace the below indexed lists with just filtering this collection
        self.nodes_by_id: dict[str, Node] = {}
        self.nodes_by_type: dict[str, list[Node]] = {}
        self.nodes_by_name: dict[str, list[Node]] = {}
        self.nodes_by_target_id: dict[str, list[Node]] = {}

        self.is_gst = os.path.splitext(path)[1] == ".gst"

        self.namespace = set_namespace_from_file(path)
        self.source_tree = ET.parse(path)
        self.library = self.source_tree.getroot().get('library') == "true"
        self.id = self.source_tree.getroot().get('id')
        self.import_ids = [c.get('targetId') for c in
                           self.source_tree.findall(f'.//{self.get_namespace_tag()}catalogueLink')]
        self.revision = self.source_tree.getroot().get('revision')
        self.game_system_revision = self.source_tree.getroot().get('gameSystemRevision')
        self.parent_map = {c: p for p in self.source_tree.iter() for c in p}

        for element in self.source_tree.findall('.//*[@id]'):
            self.create_node_from_element(element)

    def __str__(self):
        return self.name

    def create_node_from_element(self, element):
        """
        Creates a node and adds it to our indexes.
        :param element:
        :return:
        """
        node = Node(self, element)
        self.nodes.append(node)
        self.nodes_by_id.update({node.id: node})
        if node.get_type() not in self.nodes_by_type.keys():
            self.nodes_by_type[node.get_type()] = []
        self.nodes_by_type[node.get_type()].append(node)

        if node.name:
            if node.name not in self.nodes_by_name.keys():
                self.nodes_by_name[node.name] = []
            self.nodes_by_name[node.name].append(node)

        if node.target_id:
            if node.target_id not in self.nodes_by_name.keys():
                self.nodes_by_target_id[node.target_id] = []
            self.nodes_by_target_id[node.target_id].append(node)

    def get_namespace_tag(self) -> str:
        return "{" + self.namespace + "}"

    def create_element(self, tag, name, parent=None, pub=None, page=None, ):
        """
        UNTESTED
        Creates a new element with ID, and adds it to the appropriate indexes. If
        :param tag:
        :param name:
        :param parent: defaults to shared<tag>s
        :param pub:
        :param page:
        :return:
        """
        if parent is None:
            shared_element_root_name = f"shared{tag[0].upper()}{tag[1:]}s"
            parent = self.source_tree.getroot().find(shared_element_root_name)
            if parent is None:
                raise Exception(f"Cannot find {shared_element_root_name} in {self.name}")

        new_element = ET.SubElement(parent, tag, attrib={'name': name, 'hidden': "false",
                                                         'id': get_random_bs_id(), 'page': page,
                                                         'publicationId': pub})
        self.create_node_from_element(new_element)
        self.parent_map[parent] = new_element
        return new_element


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
