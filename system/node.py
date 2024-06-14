from typing import TYPE_CHECKING
from xml.etree import ElementTree as ET

from book_reader.raw_entry import RawProfile, RawModel, RawUnit, HasOptionsMixin
from system.constants import SystemSettingsKeys, SpecialRulesType
from util.element_util import get_tag, get_or_create_sub_element, get_sub_element
from util.log_util import print_styled, STYLES

if TYPE_CHECKING:
    from system.system_file import SystemFile

bsc_error_label = "!BSC Errors from "  # Trailing space will be followed by timestamp


class Node:

    def __init__(self, system_file: 'SystemFile', element: ET.Element, parent: 'Node' = None):
        self._element = element
        self.name = None
        self.id = element.attrib.get('id')
        self.target_id = element.attrib.get('targetId')
        self.condition_search_id = element.attrib.get("childId")  # Conditions use childID instead of targetId
        self.tag = element.tag
        if "}" in self.tag:
            self.tag = self.tag.split('}')[1]  # If we don't have the prefix set, tag will have the verbose namespace.
        self.type_name = element.attrib.get('typeName', element.attrib.get('type'))  # typeName on profiles, type on SEs

        self.system_file = system_file
        self.system_file.all_nodes.append(self)
        self.system_file.system.all_nodes.append(self)

        if self.id:
            self.system_file.nodes_with_ids.append(self)
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
        self.collective = (self.attrib.get("collective") == "true")

        self.children = []
        for child in element:
            Node(system_file, child, parent=self)
            # Each node will add itself to self.children with the parent check above.

        self.non_error_comments = ""
        self.previous_errors = ""
        self.previous_errors_timestamp = ""
        self.clean_previous_errors()

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
    def target_name(self):
        target_id = self.target_id if self.target_id is not None else self.condition_search_id
        return self.system.nodes_with_ids.get(lambda x: x.id == target_id).name

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

    def get_child(self, tag, attrib: dict[str:str] = None):
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

    def get_profile_node(self):
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
            return
        for child in links._element:
            if not child.tag.endswith('categoryLink'):
                continue
            categories.append(child.get('targetId'))
        return categories

        return self.system.nodes_with_ids.get(lambda x: x.id == profile_link.target_id)

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
                "Unit Type": profile.unit_type_text
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
            group_entry = option_entries.get_or_create_child('selectionEntryGroup', attrib={
                'name': group.title,
            })
            for option in group.options:
                group_entry.create_wargear_or_option(option.name, pts=option.pts,
                                                     min_n=0, max_n=group.max,
                                                     owner_name=raw_with_options.name
                                                     )

            group_entry.set_constraints_from_object(group)

    def set_wargear(self, raw_model: 'RawModel'):
        if len(raw_model.default_wargear) == 0:
            return
        for wargear_name in raw_model.default_wargear:
            self.create_wargear_or_option(wargear_name, owner_name=raw_model.name)

    def create_wargear_or_option(self, name, pts=None, min_n=1, max_n=1, default_n=None, owner_name=None):
        # Lookup option in page and get local options
        found_locally = False
        if found_locally:
            # TODO: Handle creating an option from a local profile if given.
            return
        # Lookup option in system
        found_name, wargear_id = self.system.get_wargear_name_and_id(name)
        if wargear_id is None:
            if owner_name is None:
                owner_name = self.name
            if self.type_name != "model":  # Bring this error out of the option group because the group names are long.
                self.parent.parent.append_error_comment(f"Could not find wargear in {self.name}")
            self.append_error_comment(f"Could not find wargear {name}", owner_name)
            if found_name != self.name:
                self.append_error_comment(f"\t Checked under {found_name}", owner_name)
            return

        # Create link:
        link = self.create_entrylink(found_name, wargear_id, pts=pts, name_override=name,
                                     min_n=min_n, max_n=max_n, default_n=default_n)
        if name.endswith("*"):
            link.append_error_comment("Name ends in a star, check the rules for special handling")

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
        return option_link

    def set_types_and_subtypes(self, raw_model: 'RawModel'):
        category_links = self.get_or_create_child('categoryLinks')

        for category_name in raw_model.type_and_subtypes:
            category_name = category_name.strip()
            if category_name not in self.system.categories:
                self.append_error_comment(f"Could not find type or subtype '{category_name}'", raw_model.name)
                continue
            target_id = self.system.categories[category_name].id
            cat_link = category_links.get_or_create_child('categoryLink',
                                                          attrib={'targetId': target_id,
                                                                  },
                                                          # Won't actually be the real name, may need an update script
                                                          defaults={'name': category_name},
                                                          )
            cat_link.attrib.update({'primary': 'false'})

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
        if bsc_error_label not in comment_node.text:
            self.non_error_comments = comment_node.text
            return
        self.non_error_comments = comment_node.text.split(bsc_error_label)[0]
        self.previous_errors_timestamp = comment_node.text.split(bsc_error_label)[1].split()[0]  # newline or space
        self.previous_errors = comment_node.text.split(bsc_error_label + self.previous_errors_timestamp)[1]
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

        timestamp_to_use = self.system.run_timestamp
        if self.previous_errors.strip() == new_errors_text.strip():
            # If we end up with the same state as the original,
            # reset the errors timestamp for git diffs
            timestamp_to_use = self.previous_errors_timestamp

        comment_node.text = self.non_error_comments + bsc_error_label + timestamp_to_use + new_errors_text
