from typing import TYPE_CHECKING
from xml.etree import ElementTree as ET

from book_reader.raw_entry import RawProfile
from system.constants import SystemSettingsKeys, SpecialRulesType
from util.element_util import get_description, get_tag

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

        self.tag = element.tag.split('}')[1]  # I think this only works because we've had a direct call to et.set_prefix
        self.type_name = element.attrib.get('typeName', element.attrib.get('type'))  # typeName on profiles, type on SEs
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

    def get_sub_elements_with_tag(self, tag):
        """
        Children are containers for multiple grandchildren, so go through the grandchildren
        :return:
        """
        elements = []
        for child_l1 in self.element:
            for child_l2 in child_l1:
                if get_tag(child_l2) == tag:
                    # To consider, these should have unique IDs, so we could pull nodes if we wanted.
                    elements.append(child_l2)
        return elements

    def get_element_container_for_tag(self, tag):
        for child_l1 in self.element:
            if get_tag(child_l1) == (tag + 's'):
                return child_l1

    def create_child(self, tag, attrib):
        return ET.SubElement(self.get_element_container_for_tag(tag), tag, attrib)

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

    def set_rules_text(self, name, text):
        self.element.attrib['name'] = name.title()
        element = self.get_rules_text_element()
        if element is not None:
            element.text = text

    def get_diffable_profile(self):
        text = f"Name: {self.name}\n"
        for child_l1 in self.element:
            if child_l1.tag.endswith('characteristics'):
                for child_l2 in child_l1:
                    if child_l2.tag.endswith('characteristic'):
                        # should only be one child, description
                        text += f"{child_l2.get('name')}: {child_l2.text}\n"
        return text

    def set_profile(self, raw_profile: RawProfile, profile_type):
        self.element.attrib['name'] = raw_profile.name.title()
        existing_characteristics = []
        # Set existing characteristic fields
        stats = raw_profile.stats
        stats.update({"Special Rules": raw_profile.get_special_rules_list()})

        if self.system_file.system.settings[SystemSettingsKeys.WEAPON_AS_DESCRIPTION]:
            description_entries = []
            for characteristic_type, value in raw_profile.stats.items():
                newline = "\n" if characteristic_type == "Notes" else ""
                description_entries.append(f"{newline}{characteristic_type}: {value}")
            stats = {"Description": "\t".join(description_entries)}

        for characteristic_element in self.get_sub_elements_with_tag('characteristic'):
            characteristic_type = characteristic_element.get('name')
            existing_characteristics.append(characteristic_type)

            if characteristic_type in stats.keys():
                characteristic_element.text = stats[characteristic_type]

        for characteristic_type, value in stats.items():
            if characteristic_type in existing_characteristics:
                continue  # This characteristic already exists, skip
            # Get the typeId from the system
            type_id = self.system_file.system.profile_characteristics[profile_type][characteristic_type]
            # add to the characteristic node
            self.create_child('characteristic', attrib={
                # characteristic nodes don't have an ID because they have a type and a parent with an ID.
                'name': characteristic_type,
                'typeId': type_id
            }).text = value
            # TODO: Handle multiple profiles
