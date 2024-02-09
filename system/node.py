from typing import TYPE_CHECKING
from xml.etree import ElementTree as ET

from book_reader.raw_entry import RawProfile, RawModel, RawUnit
from system.constants import SystemSettingsKeys, SpecialRulesType
from util.element_util import get_tag, get_or_create_sub_element

if TYPE_CHECKING:
    from system.system_file import SystemFile


class Node:

    def __init__(self, system_file: 'SystemFile', element: ET.Element, parent: 'Node' = None):
        self._element = element
        self.name = None
        self.id = element.attrib.get('id')
        self.target_id = element.attrib.get('targetId')
        self.tag = element.tag
        if "}" in self.tag:
            self.tag = self.tag.split('}')[1]  # If we don't have the prefix set, tag will have the verbose namespace.
        self.type_name = element.attrib.get('typeName', element.attrib.get('type'))  # typeName on profiles, type on SEs

        self.system_file = system_file
        if self.id:
            self.system_file.system.nodes_with_ids.append(self)

        if not self.is_link():
            self.name = element.attrib.get('name')

        self.parent = parent
        self.shared = False
        if self.parent is not None:
            self.parent.children.append(self)
            parent_tag = self.parent.tag
            if "}" in parent_tag:
                parent_tag = parent_tag.split('}')[1]
            self.shared = parent_tag.startswith('shared')
        self.children = []
        for child in element:
            self.children.append(Node(system_file, child, parent=self))

    @property
    def attrib(self) -> dict:
        return self._element.attrib

    @attrib.setter
    def attrib(self, value: dict):
        self._element.attrib = value

    def update_attributes(self, attrib: {}):
        for attr, value in attrib.items():
            if attr == "targetId":
                self.target_id = value
            if attr == "name":
                self.name = value
            if attr == "type":
                self.type_name = value
            if attr == "typeName":
                self.type_name = value
            attrib[attr] = str(value)  # All values must be strings to serialize properly.
        self.attrib.update(attrib)

    def update_pub_and_page(self, page: 'Page'):
        self.update_attributes({
            'page': page.page_number,
            'publicationId': page.book.pub_id
        })

    @property
    def text(self):
        return self._element.text

    @text.setter
    def text(self, value):
        self._element.text = value

    @property
    def system(self) -> 'System':
        return self.system_file.system

    def __str__(self):

        identifier_string = f"{self.type} {self.id} in {self.system_file}"
        if self.is_link():
            return f"Link to {self.target_id} ({identifier_string})"
        return f"{self.name} ({identifier_string})"

    @property
    def type(self):
        if self.type_name:
            return f"{self.tag}:{self.type_name}"
        return self.tag

    def is_link(self):
        return self.target_id is not None

    def set_target_id(self, new_target_id):
        self.target_id = new_target_id
        self._element.attrib['targetId'] = new_target_id

    def remove(self, child: 'Node'):
        self._element.remove(child._element)

    def delete(self):
        self.parent.remove(self)

    def get_sub_elements_with_tag(self, tag):
        """
        Children are containers for multiple grandchildren, so go through the grandchildren
        :return:
        """
        elements = []
        for child_l1 in self._element:
            for child_l2 in child_l1:
                if get_tag(child_l2) == tag:
                    # To consider, these should have unique IDs, so we could pull nodes if we wanted.
                    elements.append(child_l2)
        return elements

    def get_element_container_for_tag(self, tag):
        for child_l1 in self._element:
            if get_tag(child_l1) == (tag + 's'):
                return child_l1

    def get_or_create_child(self, tag, attrib: dict[str:str] = None, defaults: dict[str:str] = None):
        if attrib:
            for attr, value in attrib.items():
                attrib[attr] = str(value)  # All values must be strings to serialize properly.

        et_element, created = get_or_create_sub_element(self._element, tag, attrib)
        if created:
            if defaults:
                et_element.attrib.update(defaults)
            return Node(self.system_file, et_element, self)

        # Not created so we should have an existing node
        for child in self.children:
            if child._element == et_element:
                return child
        raise Exception(f"While looking for {tag}, we expected {et_element.tag}"
                        f"to exist in {[child.tag for child in self.children]}\n"
                        f"The node's child list is not properly being updated")

    def get_description(self):
        element = self.get_description_element()
        if element is not None:
            return element.text

    def get_description_element(self):
        for child in self._element:
            if child.tag.endswith('description'):
                return child

    def get_rules_text_element(self):
        if self.system_file.system.settings[SystemSettingsKeys.SPECIAL_RULE_TYPE] == SpecialRulesType.RULE:
            return self.get_description_element()
        else:
            for child_l1 in self._element:
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
        self._element.attrib['name'] = name.title()
        element = self.get_rules_text_element()
        if element is not None:
            element.text = text

    def get_diffable_profile(self):
        text = f"Name: {self.name}\n"
        for child_l1 in self._element:
            if child_l1.tag.endswith('characteristics'):
                for child_l2 in child_l1:
                    if child_l2.tag.endswith('characteristic'):
                        # should only be one child, description
                        text += f"{child_l2.get('name')}: {child_l2.text}\n"
        return text

    def set_profile(self, raw_profile: RawProfile, profile_type):
        self._element.attrib['name'] = raw_profile.name.title()
        existing_characteristics = []
        # Set existing characteristic fields
        stats = raw_profile.stats
        if raw_profile.special_rules:
            stats.update({"Special Rules": raw_profile.get_special_rules_list()})

        if self.system_file.system.settings[SystemSettingsKeys.WEAPON_AS_DESCRIPTION]:
            description_entries = []
            for characteristic_type, value in raw_profile.stats.items():
                newline = "\n" if characteristic_type == "Notes" else ""
                description_entries.append(f"{newline}{characteristic_type}: {value}")
            stats = {"Description": "\t".join(description_entries)}

        self.set_characteristics_from_dict(stats)

        # TODO: Handle multiple profiles

    def set_force_org(self, raw_unit: 'RawUnit'):
        category_links = self.get_or_create_child('categoryLinks')
        category_links.get_or_create_child('categoryLink',
                                           attrib={'targetId': '36c3-e85e-97cc-c503',
                                                   'name': 'Unit:',
                                                   'primary': 'false',
                                                   },
                                           )
        if raw_unit.force_org:
            if raw_unit.force_org in self.system.game.category_book_to_full_name_map:
                category_name = self.system.game.category_book_to_full_name_map[raw_unit.force_org]
                if category_name:  # Could be none for dedicated transport.
                    if category_name not in self.system.categories:
                        self.system.errors.append(f"Could not find '{category_name}' for '{raw_unit.name}'")
                    target_id = self.system.categories[category_name]
                    category_links.get_or_create_child('categoryLink',
                                                       attrib={'targetId': target_id,
                                                               'primary': 'true',
                                                               },

                                                       # Won't actually be the real name, may need an update script
                                                       defaults={'name': category_name},
                                                       )

    def set_models(self, raw_unit: 'RawUnit'):
        if len(raw_unit.model_profiles) == 0:
            return
        selection_entries = self.get_or_create_child('selectionEntries')
        for raw_model in raw_unit.model_profiles:
            model_se = selection_entries.get_or_create_child('selectionEntry',
                                                             attrib={
                                                                 "type": "model",
                                                                 "name": raw_model.name,
                                                             }, )
            model_se.update_pub_and_page(raw_unit.page)
            model_se.set_model_profile(raw_model)
            model_se.set_constraints_from_object(raw_model)
            model_se.set_wargear(raw_model)
            model_se.set_options(raw_model.options_groups)

    def set_model_profile(self, profile: 'RawProfile' or 'RawModel'):
        # There should only be one profile per entrylink, so don't filter by name.
        # In the future we may want to consider breaking if we find an infolink that's the name of the profile
        profiles_element = self.get_or_create_child('profiles')
        profile_element = profiles_element.get_or_create_child('profile')

        profile_type = "Weapon"  # assume weapon by default
        characteristics_dict = dict(profile.stats)
        if type(profile) is RawModel:
            profile_type = "Unit"  # Default to unit.
            if set(characteristics_dict.keys()) == set(self.system.game.ALT_UNIT_PROFILE_TABLE_HEADERS):
                profile_type = self.system.game.ALT_PROFILE_NAME
            characteristics_dict.update({
                "Unit Type": profile.unit_type_text
            })
        profile_element.update_attributes({'name': profile.name,
                                           'typeId': self.system.get_profile_type_id(profile_type)})

        profile_element.set_characteristics_from_dict(characteristics_dict, profile_type)

    def set_characteristics_from_dict(self, profile: dict, profile_type: str = None):
        characteristics = self.get_or_create_child('characteristics')
        for characteristic, value in profile.items():
            name, characteristic_id = self.system.get_characteristic_name_and_id(characteristic, profile_type)
            char_element = characteristics.get_or_create_child('characteristic',
                                                               attrib={'typeId': characteristic_id,
                                                                       'name': name,
                                                                       })
            char_element.text = value

    def set_constraints_from_object(self, object_with_min_max):
        if not (hasattr(object_with_min_max, 'min') and hasattr(object_with_min_max, 'max')):
            raise ValueError("The object must have min and max to set constraints")
        self.set_constraints(minimum=object_with_min_max.min, maximum=object_with_min_max.max)

    def set_constraints(self, minimum=None, maximum=None):
        constraints_el = self.get_or_create_child('constraints')
        constraint_attributes = {'field': "selections",
                                 'scope': "parent",
                                 'shared': "true",
                                 }
        if minimum is not None and minimum > 0:
            constraints_el.get_or_create_child('constraint',

                                               attrib={'type': 'min',
                                                       'value': minimum,
                                                       } | constraint_attributes,
                                               )
        if maximum is not None:
            constraints_el.get_or_create_child('constraint',

                                               attrib={'type': 'max',
                                                       'value': maximum,
                                                       } | constraint_attributes,
                                               )

    def set_cost(self, points: int or str):
        costs = self.get_or_create_child('costs')
        cost = costs.get_or_create_child('cost')
        cost.update_attributes({
            'name': "Pts",
            'typeId': "d2ee-04cb-5f8a-2642",
            'value': points,
        })

    def set_name_modifier(self, name: str):
        mods = self.get_or_create_child('modifiers')
        name_mod = mods.get_or_create_child('modifier', attrib={
            'type': "set",
            'field': "name",
        })
        name_mod.update_attributes({'value': name})

    def set_rule_info_links(self, rule_names: list):
        if len(rule_names) == 0:
            return
        info_links = self.get_or_create_child('infoLinks')

        for rule_name in rule_names:
            found_name, rule_id = self.system.get_rule_name_and_id(rule_name)
            if rule_id is None:
                continue
            rule_link = info_links.get_or_create_child('infoLink', attrib={
                'name': found_name,  # Name *should* be accurate as we're looking for it in the list
                'hidden': 'false',
                'type': 'rule',
                'targetId': rule_id,
            })
            if found_name != rule_name:
                rule_link.set_name_modifier(rule_name)

    def set_rules(self, rules_dict: dict):
        if len(rules_dict) == 0:
            return
        rules = self.get_or_create_child('rules')

    def set_options(self, option_groups: list['OptionGroup']):
        if len(option_groups) == 0:
            return
        option_entries = self.get_or_create_child('selectionEntryGroups')
        for group in option_groups:
            group_entry = option_entries.get_or_create_child('selectionEntryGroup', attrib={
                'name': group.title,
            })
            for option in group.options:
                # Lookup option in page and get local options
                found_locally = False
                if found_locally:
                    continue
                # Lookup option in system
                found_name, wargear_id = self.system.get_wargear_name_and_id(option.name)
                if wargear_id is None:
                    continue
                # Create link:
                group_entry.create_entrylink(found_name, wargear_id, pts=option.pts, name_override=option.name,
                                             min_n=0, max_n=group.max)

            group_entry.set_constraints_from_object(group)

    def set_wargear(self, raw_model: 'RawModel'):
        if len(raw_model.default_wargear) == 0:
            return
        for wargear_name in raw_model.default_wargear:
            # Lookup option in page and get local options
            found_locally = False
            if found_locally:
                continue
            # Lookup option in system
            found_name, wargear_id = self.system.get_wargear_name_and_id(wargear_name)
            if wargear_id is None:
                continue

            # Create link:
            self.create_entrylink(found_name, wargear_id, name_override=wargear_name)

    def create_entrylink(self, name, target_id, pts=None, min_n=1, max_n=1, name_override=None, default_n=None):
        entry_links = self.get_or_create_child('entryLinks')
        option_link = entry_links.get_or_create_child('entryLink', attrib={
            'name': name,
            'hidden': 'false',
            'type': 'selectionEntry',
            'targetId': target_id,
            # TODO: Set as default if should be default (need to set that in RawEntry)
        })
        if pts and pts > 0:
            option_link.set_cost(pts)
        if name_override and name_override != name:
            option_link.set_name_modifier(name_override)
        option_link.set_constraints(min_n, max_n)
