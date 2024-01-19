from typing import TYPE_CHECKING
from xml.etree import ElementTree as ET

if TYPE_CHECKING:
    from system.system_file import SystemFile


class Node:

    def __init__(self, system_file: 'SystemFile', element: ET.Element):
        self.deleted = None
        self.name = None

        self.system_file = system_file
        self.element = element
        self.id = element.attrib.get('id')
        if not self.id:
            raise Exception("Node initialization attempted on element with no ID")

        self.target_id = element.attrib.get('targetId')

        self.tag = element.tag.split('}')[1]
        if not self.is_link():
            self.name = element.attrib.get('name')
        self.parent = self.get_parent_element()
        self.shared = False
        if self.parent:
            self.shared = self.parent.tag.split('}')[1].startswith('shared')

    def is_link(self):
        return self.target_id is not None

    def set_target_id(self, new_target_id):
        self.target_id = new_target_id
        self.element.attrib['targetId'] = new_target_id

    def delete(self):
        self.get_parent_element().remove(self.element)
        self.deleted = True
        # Difficult to go through all the lists and clean up, so doing this as a temporary measure

    def get_parent_element(self):
        return self.system_file.parent_map[self.element]

    def get_grandparent(self):
        """
        The parent is generally just a container for that type of node,
        so get the grandparent if we need to add a node of another type.
        :return:
        """
        return self.system_file.parent_map[self.get_parent_element()]
