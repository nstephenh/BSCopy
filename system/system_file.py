import os
from typing import TYPE_CHECKING
from xml.etree import ElementTree as ET

from system.node import Node
from system.node_collection import NodeCollection
from util.generate_util import cleanup_file_match_bs_whitespace
from util.text_utils import make_plural

if TYPE_CHECKING:
    from system.system import System


class SystemFile:

    def __init__(self, system: 'System', path):
        self.system = system  # Link to parent
        self.name = os.path.split(path)[1]
        self.path = path

        self.is_gst = os.path.splitext(path)[1] == ".gst"
        self.is_template = "Template" in self.name

        self.namespace = set_namespace_from_file(path)

        self.all_nodes = NodeCollection([])
        self.nodes_with_ids = NodeCollection([])
        self._source_tree = ET.parse(path)

        self.library = self._source_tree.getroot().get('library') == "true"
        self.id = self._source_tree.getroot().get('id')
        self.import_ids = [c.get('targetId') for c in
                           self._source_tree.findall(f'.//{self.get_namespace_tag()}catalogueLink')]
        self.revision = self._source_tree.getroot().get('revision')
        self.game_system_revision = self._source_tree.getroot().get('gameSystemRevision')

        self._parent_map = {c: p for p in self._source_tree.iter() for c in p}
        self.root_node = Node(self, self._source_tree.getroot(), is_root_node=True)

    def save(self):
        ET.indent(self._source_tree)
        # utf-8 to keep special characters un-escaped.
        self._source_tree.write(self.path, encoding="utf-8")
        cleanup_file_match_bs_whitespace(self.path)

    def __str__(self):
        return self.name

    def get_namespace_tag(self) -> str:
        return "{" + self.namespace + "}"

    def get_or_create_shared_node(self, tag: str, attrib: dict = None) -> 'Node':
        """
        Create a node under this file's sharedPlural({tag})
        :return: The created node
        """
        parent_tag = tag
        shared_element_root_tag = f"shared{parent_tag[0].upper()}{make_plural(parent_tag[1:])}"
        parent = self.root_node.get_or_create_child(shared_element_root_tag)
        return parent.get_or_create_child(tag, attrib)

    @property
    def faction(self):
        pretty_name = self.root_node.name
        if not self.system.game:
            return None
        if pretty_name in self.system.game.FACTIONS:
            return pretty_name
        if " - " in pretty_name:
            name_component = pretty_name.split(" - ")[1]
            name_component = name_component.strip()
            if name_component in self.system.game.FACTIONS:
                return name_component


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


def read_categories(source_tree):
    category_map = {}
    categories_element = source_tree.find("{http://www.battlescribe.net/schema/catalogueSchema}categoryEntries")
    if not categories_element:
        categories_element = source_tree.find("{http://www.battlescribe.net/schema/gameSystemSchema}categoryEntries")
        if not categories_element:
            return
    for category_element in categories_element:
        name = category_element.get('name')
        if name.endswith(":"):
            name = name[:-1]
        if name.lower().endswith(" sub-type"):
            name = name[:-len(" sub-type")]
            if name.lower().endswith(" unit"):
                name = name[:-len(" unit")]
        elif name.lower().endswith(" unit-type"):
            name = name[:-len(" unit-type")]
        id = category_element.get('id')
        category_map[name] = id
    return category_map
