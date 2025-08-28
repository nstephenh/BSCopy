from typing import Callable
from typing import TYPE_CHECKING
from xml.etree import ElementTree as ET

from book_reader.raw_entry import RawProfile, RawModel, RawUnit
from system.constants import SystemSettingsKeys, SpecialRulesType
from system.game.heresy3e import Heresy3e
from util.element_util import get_tag, get_or_create_sub_element, get_sub_element
from util.generate_util import find_comment_value
from util.log_util import print_styled, STYLES

if TYPE_CHECKING:
    from system.system_file import SystemFile

bsc_error_label = "warning: !BSC "  # Trailing space will be followed by timestamp


class Node:

    def __init__(self, system_file: 'SystemFile', element: ET.Element, parent: 'Node' = None, is_root_node=False):
        self._element = element
        self.name = None
        self.id = element.attrib.get('id')
        self.target_id = element.attrib.get('targetId')
        self.condition_search_id = element.attrib.get("childId")  # Conditions use childID instead of targetId
        self.tag = element.tag
        if "}" in self.tag:
            self.tag = self.tag.split('}')[1]  # If we don't have the prefix set, tag will have the verbose namespace.
        self.type_name = element.attrib.get('typeName', element.attrib.get('type'))  # typeName on profiles, type on SEs

        self.pub = self.attrib.get('publicationId')
        self.page = self.attrib.get('page')

        self.system_file = system_file
        self.system_file.all_nodes.append(self)
        self.system_file.system.all_nodes.append(self)

        self.value = element.attrib.get('value')
        self.field = element.attrib.get('field')
        self.condition_scope = element.attrib.get('scope')
        self.condition_percentValue = element.attrib.get('percentValue')
        self.includeChildSelections = element.attrib.get('includeChildSelections')
        self.includeChildForces = element.attrib.get('includeChildForces')

        self.start_line_number = None
        self.end_line_number = None
        if self.system.settings.get("diff"):
            self.start_line_number = element._start_line_number
            self.end_line_number = element._end_line_number

        if self.id:
            self.system_file.nodes_with_ids.append(self)
            self.system_file.system.nodes_with_ids.append(self)

        if not self.is_link():
            self.name = element.attrib.get('name')

        self.parent = parent
        self.shared = False
        self.is_root_node = is_root_node
        self.is_base_level = False  # mostly for root selection entries
        if self.parent is not None:
            self.parent.children.append(self)
            parent_tag = self.parent.tag
            if "}" in parent_tag:
                parent_tag = parent_tag.split('}')[1]
            self.shared = parent_tag.startswith('shared')
            if self.parent and self.parent.parent:
                # self.parent.parent as the parent would be "selectionEntries"
                self.is_base_level = self.parent.parent.is_root_node

        self.collective = (self.attrib.get("collective") == "true")

        self.children = []
        for child in element:
            Node(system_file, child, parent=self)
            # Each node will add itself to self.children with the parent check above.

        self.non_error_comments = ""
        self.previous_errors = ""
        self.previous_errors_timestamp = ""
        self.clean_previous_errors()

        # Certain nodes that didn't generally get ids, namely modifiers and conditions,
        # were given ids by BSCopy to make them easier to find.
        self.bscopy_node_id = ""
        if "node_id_" in self.non_error_comments:
            self.bscopy_node_id = find_comment_value(self._element,
                                                     node_id=True)  # old code, it's "node" is an element.
        self.template_id = ""
        if "template_id_" in self.non_error_comments:
            self.template_id = find_comment_value(self._element)  # old code, it's "node" is an element.

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
            if type(value) == bool:
                attrib[attr] = str(value).lower()
        self.attrib.update(attrib)

    def update_pub_and_page(self, page: 'Page'):
        existing_pub_id = self.attrib.get('publicationId')
        if existing_pub_id:
            existing_priority = self.system.raw_pub_priority.get(existing_pub_id)
            if existing_priority is None:
                print_styled("We have updated a rule from a book we didn't import", STYLES.RED)
            else:
                if page.book.priority < existing_priority:
                    return  # Do not update a publication if the other source has higher priority
        self.update_attributes({
            'page': page.page_number,
            'publicationId': page.book.pub_id
        })
        self.page = page.page_number
        self.pub = page.book.pub_id

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
        location_string = f"in {self.system_file}"
        if not self.is_base_level or not self.is_root_node:
            location_string = f"on {self.root_name} {location_string}"
        if self.root_name != self.parent_name:
            location_string = f"for {self.parent_name} {location_string}"

        identifier_string = f"{self.type} {location_string}"
        if self.id:
            identifier_string += f", id: {self.id}"
        if self.generated_name:
            return f"{self.generated_name} ({identifier_string})"
        if self.condition_search_id:
            return f"{self.type} {self.value} of {self.target_name} ({location_string})"

        return identifier_string

    @property
    def simple_identifier(self):
        identifier_string = f"{self.type}"
        if self.id:
            identifier_string += f"({self.id})"
        return identifier_string

    @property
    def path(self):
        if self.parent:
            return f"{self.parent.path} > {self.simple_identifier}"
        return self.simple_identifier

    @property
    def parent_model(self):
        if self.parent:
            if self.parent.type_name == "model":
                return self.parent.name
            return self.parent.parent_model
        return None

    @property
    def parent_unit(self):
        if self.parent:
            if self.parent.type_name == "unit":
                return self.parent.name
            return self.parent.parent_unit
        return None

    @property
    def target_name(self):
        target_id = self.target_id if self.target_id is not None else self.condition_search_id
        return self.system.try_get_name(target_id)

    @property
    def target(self):
        target_id = self.target_id if self.target_id is not None else self.condition_search_id
        return self.system.nodes_with_ids.get(lambda x: x.id == target_id)

    @property
    def parent_name(self):
        if self.parent is None:
            return None
        if self.parent.target_id:
            return self.parent.target_name
        if self.parent.name:
            return self.parent.name
        return self.parent.parent_name

    @property
    def root_name(self):
        if self.is_base_level:
            return self.name
        if self.parent is None:
            return None
        return self.parent.root_name

    @property
    def type(self):
        if self.type_name:
            return f"{self.tag}:{self.type_name}"
        return self.tag

    @property
    def generated_name(self):
        if self.is_link():
            return f"Link to {self.target_name}"
        if self.tag == "condition":
            return f"{self.type_name} {self.value} of {self.target_name} in {self.system.try_get_name(self.condition_scope)}"
        if self.tag == "conditionGroup":
            return f"{self.type_name}"
        if self.tag == "modifier":
            conjunction = "to"  # set
            if self.type_name == "increment":
                conjunction = "by"
            if self.type_name == "append":
                return f"{self.type_name} {self.value} to {self.system.try_get_name(self.field)}"
            return f"{self.type_name} {self.system.try_get_name(self.field)} {conjunction} {self.system.try_get_name(self.value)}"
        if self.tag == "constraint":
            name = f"{self.type_name} {self.value} {self.field} of {self.target_name}"
            if self.condition_scope:
                name = f"{name} in {self.system.try_get_name(self.condition_scope)}"
            return name
        return self.name

    @property
    def pretty_single(self):
        if self.tag in ["conditions", "conditionGroups", "modifiers", "constraints"]:
            return None  # These should not print at all in pretty print mode, and thus don't get an indent level
        return self.generated_name

    def pretty_full(self, indent=0):
        full_string = ""
        self_string = self.pretty_single
        if self_string is not None:
            full_string = f"{'-' * indent}{self_string}" + "\n"
            indent += 1
        for child in self.children:
            child_string = child.pretty_full(indent=indent)
            if child_string:  # Some children get skipped
                full_string += child_string
        return full_string

    def is_link(self):
        return self.target_id is not None

    def set_target_id(self, new_target_id):
        self.target_id = new_target_id
        self._element.attrib['targetId'] = new_target_id

    def remove(self, child: 'Node'):
        if child.parent != self:
            raise Exception("Cannot remove a node from something that's not it's parent")
        child.parent = None
        self._element.remove(child._element)  # Remove from XML
        self.children.remove(child)  # Remove from list of children in the python view
        # The node is still likely in all nodes list. Do we want this (for copying?)

    def delete(self):
        self.parent.remove(self)

    def move_node_to_here(self, moving_node: 'Node'):
        self._element.append(moving_node._element)  # Copy the xml element
        moving_node.delete()  # Delete the xml element,
        moving_node.parent = self
        self.children.append(moving_node)

    def find_ancestor_with(self, condition_function: Callable[['Node'], bool]):
        if not self.parent:
            return None
        if condition_function(self.parent):
            return self.parent
        return self.parent.find_ancestor_with(condition_function)

    def does_descendent_exist(self, condition_function: Callable[['Node'], bool]):
        """
        Depth-first search to find if a child fulfils a particular condition.
        :param condition_function:
        :return:
        """
        if len(self.children) == 0:
            return False
        for child in self.children:
            if condition_function(child):
                return True
            if child.does_descendent_exist(condition_function):
                return True
        return False

    def get_descendants_with(self, condition_function: Callable[['Node'], bool]):
        """
        Depth-first search to find if a child fulfils a particular condition.
        :param condition_function:
        :return:
        """
        matching_nodes = []
        for child in self.children:
            if condition_function(child):
                matching_nodes.append(child)
            matching_nodes += child.get_descendants_with(condition_function)
        return matching_nodes

    @property
    def is_wargear_link(self):
        if not self.is_link():
            return False
        return self.system.nodes_with_ids.get(lambda x: x.id == self.target_id).is_wargear_se

    @property
    def is_wargear_se(self):
        return self.get_child("profiles") and (
                self.get_child("profiles").get_child("profile", attrib={"typeName":
                                                                            self.system.game.WARGEAR_PROFILE_NAME})
                or
                self.get_child("profiles").get_child("profile", attrib={"typeName": "Weapon"})
        )

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

    def get_child(self, tag, attrib: dict[str:str] = None) -> 'Node' or None:
        et_element = get_sub_element(self._element, tag, attrib)
        for child in self.children:
            if child._element == et_element:
                return child

    def get_rules_text_element(self):
        if self.system_file.system.settings[SystemSettingsKeys.SPECIAL_RULE_TYPE] == SpecialRulesType.RULE:
            return self.get_or_create_child('description')
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

    def set_rules_text(self, text):
        element = self.get_rules_text_element()
        if element is not None:
            element.text = text

    def get_profile_node(self, type_name=None) -> 'Node':
        """
        Returns the first profile node in this node, or the first linked profile from this node.
        :return:
        """
        profiles = self.get_child('profiles')
        if profiles is None:
            links = self.get_child('infoLinks')
            if links is None:
                return
            profile_link = links.get_child('infoLink', {"type": "profile"})
            if profile_link is None:
                return
            return self.system.nodes_with_ids.get(lambda x: x.id == profile_link.target_id)
        if type_name:
            return profiles.get_child('profile', attrib={'typeName': type_name})
        return profiles.get_child('profile')

    def get_profile_dict(self):
        profile_as_dict = {"Name": self.name}
        for child_l1 in self._element:
            if child_l1.tag.endswith('characteristics'):
                for child_l2 in child_l1:
                    if child_l2.tag.endswith('characteristic'):
                        # should only be one child, description
                        profile_as_dict[child_l2.get('name')] = child_l2.text
        return profile_as_dict

    def get_categories(self):
        categories = []
        links = self.get_child('categoryLinks')
        if links is None:
            return []
        for child in links._element:
            if not child.tag.endswith('categoryLink'):
                continue
            categories.append(child.get('targetId'))
        return categories

    def set_profile_characteristics(self, raw_profile: RawProfile, profile_type):
        self._element.attrib['name'] = raw_profile.name
        existing_characteristics = []
        # Set existing characteristic fields
        stats = raw_profile.stats
        # Hardcoded switch between heresy and the old world, if we expand this script will need additional updating.
        if raw_profile.special_rules and "Type" not in stats.keys():
            stats.update({"Special Rules": raw_profile.get_special_rules_list()})

        if self.system_file.system.settings[SystemSettingsKeys.WEAPON_AS_DESCRIPTION]:
            description_entries = []
            for characteristic_type, value in raw_profile.stats.items():
                newline = "\n" if characteristic_type == "Notes" else ""
                description_entries.append(f"{newline}{characteristic_type}: {value}")
            stats = {"Description": "\t".join(description_entries)}

        self.set_characteristics_from_dict(stats, profile_type)
        self.update_pub_and_page(raw_profile.page)

        # TODO: Handle multiple profiles

    def set_force_org(self, raw_unit: 'RawUnit'):
        if self.system.game.GAME_FORMAT_CONSTANT == Heresy3e.GAME_FORMAT_CONSTANT:
            return
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
                        self.append_error_comment(f"Could not find '{category_name}'", raw_unit.name)
                    target_id = self.system.categories[category_name].id
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
            model_se.set_rule_info_links(raw_model)
            model_se.set_wargear(raw_model)
            model_se.set_options(raw_model)
            model_se.set_types_and_subtypes(raw_model)

    def set_model_profile(self, profile: 'RawModel'):
        # There should only be one profile per entrylink, so don't filter by name.
        # In the future we may want to consider breaking if we find an infolink that's the name of the profile
        profiles_element = self.get_or_create_child('profiles')
        profile_element = profiles_element.get_or_create_child('profile')

        profile_type = None
        characteristics_dict = dict(profile.stats)
        if type(profile) is RawModel:
            profile_type = profile.profile_type
            characteristics_dict.update({
                self.system.game.MODEL_TYPE_CHARACTERISTIC: profile.unit_type_text
            })
        if profile_type is None:
            raise Exception(f"Could not find profile type for {profile.profile_type}")
        profile_element.update_attributes({'name': profile.name,
                                           'typeId': self.system.get_profile_type_id(profile_type)})

        profile_element.set_characteristics_from_dict(characteristics_dict, profile_type)

        if hasattr(profile, 'pts'):
            self.set_cost(profile.pts)

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

    def set_rule_info_links(self, raw_profile: RawProfile):
        if len(raw_profile.special_rules) == 0:
            return
        info_links = self.get_or_create_child('infoLinks')

        for rule_name in raw_profile.special_rules:
            found_name, rule_id = self.system.get_rule_name_and_id(rule_name)
            if rule_id is None:
                self.append_error_comment(f"Could not find rule: {rule_name}", raw_profile.name)
                continue
            rule_link = info_links.get_or_create_child('infoLink', attrib={
                'name': found_name,  # Name *should* be accurate as we're looking for it in the list
                'hidden': 'false',
                'type': 'rule',
                'targetId': rule_id,
            })
            if found_name != rule_name:
                rule_link.set_name_modifier(rule_name)

    def set_rules(self, raw_unit: 'RawUnit'):
        if len(raw_unit.special_rule_descriptions) == 0:
            return
        for rule, text in raw_unit.special_rule_descriptions.items():
            self.create_rule(rule, text, raw_unit.page)

    def set_options(self, raw_with_options: RawUnit or RawModel):
        option_groups = raw_with_options.option_groups
        if len(option_groups) == 0:
            return
        option_entries = self.get_or_create_child('selectionEntryGroups')
        for group in option_groups:
            option_entries.create_option_group(group, raw_with_options.name)

    def create_shared_option_group(self, group):
        option_entries = self.get_or_create_child('sharedSelectionEntryGroups')
        option_entries.create_option_group(group, self.system_file.name)

    def create_option_group(self, group, owner_name):
        group_entry = self.get_or_create_child('selectionEntryGroup', attrib={
            'name': group.title,
        })
        for option in group.options:
            group_entry.create_wargear_or_option(option.name, pts=option.pts,
                                                 min_n=0, max_n=group.max,
                                                 owner_name=owner_name
                                                 )
        group_entry.set_constraints_from_object(group)

    def set_wargear(self, raw_model: 'RawModel'):
        if len(raw_model.default_wargear) == 0:
            return
        for wargear_name in raw_model.default_wargear:
            self.create_wargear_or_option(wargear_name, owner_name=raw_model.name)

    def create_wargear_or_option(self, name, pts=None, min_n=1, max_n=1, default_n=None, owner_name=None):
        # Lookup option in page and get local options
        name_override = None
        found_locally = False
        if found_locally:
            # TODO: Handle creating an option from a local profile if given.
            return
        if name.startswith("item from the"):
            list_name = name.split("item from the")[1]
            if " list" in list_name:
                list_name = list_name.split(" list")[0]
            list_name = list_name.strip()
            list_node = self.system.get_wargear_list_node_by_name(list_name)
            if list_node is None:
                self.append_error_comment(f"Could not find wargear list '{list_name}'", owner_name)
                return
            wargear_id = list_node.id
            found_name = list_node.name
        else:
            # Lookup option in system
            found_name, wargear_id = self.system.get_wargear_name_and_id(name)
            name_override = name
            if wargear_id is None:
                if owner_name is None:
                    owner_name = self.name
                if self.type_name != "model":
                    # Bring this error out of the option group because the group names are long.
                    self.parent.parent.append_error_comment(f"Could not find wargear in {self.name}")
                self.append_error_comment(f"Could not find wargear {name}", owner_name)
                if found_name != self.name:
                    self.append_error_comment(f"\t Checked under {found_name}", owner_name)
                return

        # Create link:
        link = self.create_entrylink(found_name, wargear_id, pts=pts, name_override=name_override,
                                     min_n=min_n, max_n=max_n, default_n=default_n)
        if name.endswith("*"):
            link.append_error_comment("Name ends in a star, check the rules for special handling")

    def create_entrylink(self, name, target_id, pts=None, min_n=1, max_n=1, name_override=None, default_n=None):
        entry_links = self.get_or_create_child('entryLinks')
        target_node = self.system.get_node_by_id(target_id)
        option_link = entry_links.get_or_create_child('entryLink', attrib={
            'hidden': 'false',
            'type': target_node.tag,
            'targetId': target_id,
            # TODO: Set as default if should be default (need to set that in RawEntry)
        })
        option_link.update_attributes({'name': target_node.name})
        if pts and pts > 0:
            option_link.set_cost(pts)
        if name_override and name_override.lower() != name.lower():
            option_link.set_name_modifier(name_override)
        option_link.set_constraints(min_n, max_n)
        return option_link

    def set_types_and_subtypes(self, raw_model: 'RawModel'):
        category_links = self.get_or_create_child('categoryLinks')

        for category_name in raw_model.type_and_subtypes:
            category_name = category_name.strip()
            if category_name not in self.system.model_types_and_subtypes:
                self.append_error_comment(f"Could not find type or subtype '{category_name}'", raw_model.name)
                continue
            category_node = self.system.model_types_and_subtypes[category_name]
            category_links.get_or_create_child('categoryLink',
                                               attrib={'targetId': category_node.id,
                                                       },
                                               defaults={'primary': 'false',
                                                         'name': category_node.name},
                                               )

    def check_types_and_subtypes(self, raw_model: 'RawModel'):
        category_links = self.get_child('categoryLinks')
        if category_links is None:
            return ["No category links"]
        errors = []
        expected_ids = []
        existing_link_count = len(category_links.children)
        correct_link_count = 0
        for category_name in raw_model.type_and_subtypes:
            category_name = category_name.strip()
            if category_name not in self.system.model_types_and_subtypes.keys():
                errors.append(f"Could not find type or subtype '{category_name}'")
                continue
            category_node = self.system.model_types_and_subtypes[category_name]
            expected_ids.append(category_node.id)
            cat_link = category_links.get_child('categoryLink',
                                                attrib={
                                                    'targetId': category_node.id,
                                                }
                                                )
            if cat_link is None:
                errors.append(f"{category_node} is not linked")
                continue
            correct_link_count += 1
        for cat_link in category_links.children:
            if cat_link.target_id not in expected_ids:
                if cat_link.target_name in self.system.game.BATTLEFIELD_ROLES:
                    errors.append(f"Models should not reference battlefield roles: {cat_link}")
                # Permissively allowing other categories.
        return errors

    def create_category(self, name, text, page):
        categories = self.get_or_create_child('categoryEntries')
        category = categories.get_or_create_child('categoryEntry',
                                                  attrib={'name': name + ":",
                                                          'hidden': 'false',
                                                          }
                                                  )
        category.create_rule(name, text, page)

    def create_rule(self, name, text, page):
        """
        Do not call on a root node as it only creates under the 'rules' subnode and not 'sharedRules'.
        :param name:
        :param text:
        :param page:
        :return:
        """
        rules = self.get_or_create_child('rules')
        rule_node = rules.get_or_create_child('rule', attrib={'name': name})
        rule_node.update_pub_and_page(page)
        rule_node.set_rules_text(text)

    def set_comments(self, text):
        if not text:
            return
        comment_node = self.get_or_create_child('comment')
        comment_node.text = text

    def clean_previous_errors(self):
        comment_node = self.get_child('comment')
        if comment_node is None:
            return
        if comment_node.text is None or comment_node.text == "":
            comment_node.delete()
            return
        if bsc_error_label in comment_node.text:
            self.non_error_comments = comment_node.text.split(bsc_error_label)[0]
            self.previous_errors_timestamp = comment_node.text.split(bsc_error_label)[1].split()[0]  # newline or space
            self.previous_errors = comment_node.text.split(bsc_error_label + self.previous_errors_timestamp)[1]
        elif "!BSC Errors from " in comment_node.text:
            self.non_error_comments = comment_node.text.split("!BSC Errors from ")[0]
            self.previous_errors_timestamp = comment_node.text.split("!BSC Errors from ")[1].split()[
                0]  # newline or space
            self.previous_errors = comment_node.text.split("!BSC Errors from " + self.previous_errors_timestamp)[1]
        else:
            self.non_error_comments = comment_node.text
            return  # Don't delete the comment node we just created and are populating

        comment_node.text = self.non_error_comments

        if comment_node.text is None or comment_node.text == "":
            comment_node.delete()

    def append_error_comment(self, error_text, heading_for_system_errors=None):
        if heading_for_system_errors is not None:
            self.system.errors.append(heading_for_system_errors + ": " + error_text)
        comment_node = self.get_or_create_child('comment')

        if comment_node.text is None:
            comment_node.text = ""

        new_errors_text = "\n" + error_text

        if bsc_error_label in comment_node.text:
            existing_timestamp = comment_node.text.split(bsc_error_label)[1].split()[0]  # newline or space
            existing_errors_text = comment_node.text.split(bsc_error_label + existing_timestamp)[1]
            new_errors_text = existing_errors_text + new_errors_text
        elif "!BSC Errors from " in comment_node.text:  # Migration from old label
            existing_timestamp = comment_node.text.split("!BSC Errors from ")[1].split()[0]  # newline
            existing_errors_text = comment_node.text.split("!BSC Errors from " + existing_timestamp)[1]
            new_errors_text = existing_errors_text + new_errors_text

        timestamp_to_use = self.system.run_timestamp
        if self.previous_errors.strip() == new_errors_text.strip():
            # If we end up with the same state as the original,
            # reset the errors timestamp for git diffs
            timestamp_to_use = self.previous_errors_timestamp

        comment_node.text = self.non_error_comments + bsc_error_label + timestamp_to_use + new_errors_text

    def set_conditional_option(self, option_child_id: str):
        self.get_or_create_child('conditions').get_or_create_child(
            "condition",
            attrib={
                "type": "atLeast",
                "value": 1,
                "field": "selections",
                "scope": "force",
                "childId": option_child_id,
                "shared": 'true',
                "includeChildSelections": 'true'
            }
        )

    def set_hidden(self):
        mods = self.get_or_create_child('modifiers')
        return mods.get_or_create_child('modifier',
                                        attrib={
                                            'type': 'set',
                                            'value': "hidden",
                                            'field': "true",
                                        })

    def modify_profile(self, new_profile, profile_type) -> bool:
        profile_node = self.get_profile_node(profile_type)
        print(profile_node)
        if not profile_node:
            self.append_error_comment(f"Profile changed type")
            return False
        existing_characteristics_node = profile_node.get_child('characteristics')
        mod_groups = profile_node.get_or_create_child('modifierGroups')
        mod_group = mod_groups.get_or_create_child('modifierGroup', attrib={'type': 'and'})
        mod_group.set_conditional_option("1231-877a-96d9-cacd")
        mods = mod_group.get_or_create_child('modifiers')
        # For each stat, create a mod if that stat has changed
        for characteristic_name, value in new_profile.stats.items():
            _, characteristic_id = self.system.get_characteristic_name_and_id(characteristic_name, profile_type)
            existing_characteristic_node = existing_characteristics_node.get_child('characteristic', attrib={
                "typeId": characteristic_id
            })
            if existing_characteristic_node.text == value:
                continue  # Value is already set

            #  <modifier type="set" value="New Range" field="95ba-cda7-b831-6066"/>
            mods.get_or_create_child('modifier',
                                     attrib={
                                         'type': 'set',
                                         'value': value,
                                         'field': characteristic_id
                                     })
        # Compare the types and add/remove special rules as needed.
        self.modify_rule_info_links(new_profile)

    def modify_rule_info_links(self, raw_profile: RawProfile):
        if len(raw_profile.special_rules) == 0:
            return
        info_links = self.get_or_create_child('infoLinks')

        for rule_name in raw_profile.special_rules:
            found_name, rule_id = self.system.get_rule_name_and_id(rule_name)
            if rule_id is None:
                self.append_error_comment(f"Could not find rule: {rule_name}", raw_profile.name)
                continue

            rule_already_existed = info_links.get_child('infoLink', attrib={
                'targetId': rule_id,
            })
            if rule_already_existed:
                print(f"Looking at existing rule {rule_name}")
                mods = rule_already_existed.get_child('modifiers')
                if not mods:
                    continue  # No mods thus no name mods.
                # What will this do if there's two?
                existing_name_mod = mods.get_child('modifier', attrib={
                    'type': "set",
                    'field': "name",
                })
                if not existing_name_mod:
                    continue  # This is not a rule with a number modifier
                if existing_name_mod.value == rule_name:
                    continue  # The name does not need to be changed as it's already set
                print(f"Rule may need changed from '{existing_name_mod.value}' to '{rule_name}'")
                self.append_error_comment(f"Rule needs changed from '{existing_name_mod.value}' to '{rule_name}'",
                                          raw_profile.name)
                continue
                existing_name = existing_name_mod.value
                name_mod = rule_link.set_name_modifier(rule_name)
                continue

            rule_link = info_links.get_or_create_child('infoLink', attrib={
                'name': found_name,  # Name *should* be accurate as we're looking for it in the list
                'hidden': 'false',
                'type': 'rule',
                'targetId': rule_id,
            })
            if found_name != rule_name:
                rule_link.set_name_modifier(rule_name)
            if not rule_already_existed:
                rule_link.set_hidden().set_conditional_option("1231-877a-96d9-cacd")
