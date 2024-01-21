from typing import TYPE_CHECKING
from xml.etree import ElementTree as ET

from system.constants import SystemSettingsKeys, SpecialRulesType
from util.element_util import get_description

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
        self.type_name = element.attrib.get('typeName')  # for profile types, at least generally
        if not self.is_link():
            self.name = element.attrib.get('name')
        self.parent = self.get_parent_element()
        self.shared = False
        if self.parent:
            self.shared = self.parent.tag.split('}')[1].startswith('shared')

    def __str__(self):
        return f"{self.name} ({self.get_type()} {self.id} in {self.system_file})"

    def get_type(self):
        if self.type_name:
            return f"{self.tag}:{self.type_name}"
        return self.tag

    def is_link(self):
        return self.target_id is not None

    def set_target_id(self, new_target_id):
        self.target_id = new_target_id
        self.element.attrib['targetId'] = new_target_id

    def delete(self):
        try:
            self.get_parent_element().remove(self.element)
        except ValueError:
            pass  # The target many have already been removed
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

    def update_attributes(self, attrib):
        self.element.attrib.update(attrib)

    def get_rules_text_element(self):
        if self.system_file.system.settings[SystemSettingsKeys.SPECIAL_RULE_TYPE] == SpecialRulesType.RULE:
            return get_description(self.element)
        else:
            for child_l1 in self.element:
                if child_l1.tag.endswith('characteristics'):
                    for child_l2 in child_l1:
                        if child_l2.tag.endswith('characteristic'):
                            # should only be one child, description
                            return child_l2

    def get_rules_text(self):
        element = self.get_rules_text_element()
        if element is not None:
            return element.text

    def set_rules_text(self, text):
        element = self.get_rules_text_element()
        if element is not None:
            element.text = text
