from xml.etree import ElementTree as ET

from book_reader.page import Page
from book_reader.raw_entry import OptionGroup, RawUnit, RawProfile, RawModel
from util.element_util import get_or_create_sub_element


class SystemElement:
    def __init__(self, system, element: ET.Element):
        self.system = system
        self._element = element

    @property
    def attrib(self):
        return self._element.attrib

    @property
    def text(self):
        return self._element.text

    @text.setter
    def text(self, value):
        self._element.text = value

    @property
    def category_book_to_full_name_map(self):
        return self.system.game.category_book_to_full_name_map

    def get_or_create(self, tag, attrib: dict[str:str] = None, assign_id: bool = False, defaults: dict[str:str] = None):
        if attrib:
            for attr, value in attrib.items():
                attrib[attr] = str(value)  # All values must be strings to serialize properly.
        element, created = get_or_create_sub_element(self._element, tag, attrib, assign_id)
        if created and defaults:
            element.attrib.update(defaults)
        return self.system.element_as_system_element(element)

    def update_attributes(self, attrib: {}):
        for attr, value in attrib.items():
            attrib[attr] = str(value)  # All values must be strings to serialize properly.
        self.attrib.update(attrib)

    def update_pub_and_page(self, page: 'Page'):
        self.update_attributes({
            'page': page.page_number,
            'publicationId': page.book.pub_id
        })

    def set_force_org(self, raw_unit: 'RawUnit'):
        category_links = self.get_or_create('categoryLinks')
        category_links.get_or_create('categoryLink',
                                     attrib={'targetId': '36c3-e85e-97cc-c503',
                                             'name': 'Unit:',
                                             'primary': 'false',
                                             },
                                     assign_id=True)
        if raw_unit.force_org:
            if raw_unit.force_org in self.category_book_to_full_name_map:
                category_name = self.category_book_to_full_name_map[raw_unit.force_org]
                if category_name:  # Could be none for dedicated transport.
                    if category_name not in self.system.categories:
                        self.system.errors.append(f"Could not find '{category_name}' for '{raw_unit.name}'")
                    target_id = self.system.categories[category_name]
                    category_links.get_or_create('categoryLink',
                                                 attrib={'targetId': target_id,
                                                         'primary': 'true',
                                                         },
                                                 assign_id=True,
                                                 # Won't actually be the real name, may need an update script
                                                 defaults={'name': category_name},
                                                 )

    def set_models(self, raw_unit: 'RawUnit'):
        if len(raw_unit.model_profiles) == 0:
            return
        selection_entries = self.get_or_create('selectionEntries')
        for raw_model in raw_unit.model_profiles:
            model_se = selection_entries.get_or_create('selectionEntry',
                                                       attrib={
                                                           "type": "model",
                                                           "name": raw_model.name,
                                                       }, assign_id=True)
            model_se.update_pub_and_page(raw_unit.page)
            model_se.set_model_profile(raw_model)
            model_se.set_constraints(raw_model)

    def set_model_profile(self, profile: 'RawProfile' or 'RawModel'):
        # There should only be one profile per entrylink, so don't filter by name.
        # In the future we may want to consider breaking if we find an infolink that's the name of the profile
        profiles_element = self.get_or_create('profiles')
        profile_element = profiles_element.get_or_create('profile')

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

    def set_characteristics_from_dict(self, profile: dict, profile_type: str):
        characteristics = self.get_or_create('characteristics')
        for characteristic, value in profile.items():
            name, characteristic_id = self.system.get_characteristic_name_and_id(profile_type, characteristic)
            char_element = characteristics.get_or_create('characteristic',
                                                         attrib={'typeId': characteristic_id,
                                                                 'name': name,
                                                                 })
            char_element.text = value

    def set_constraints(self, object_with_min_max):
        if not (hasattr(object_with_min_max, 'min') and hasattr(object_with_min_max, 'max')):
            raise ValueError("The object must have min and max to set constraints")
        constraints_el = self.get_or_create('constraints')
        constraint_attributes = {'field': "selections",
                                 'scope': "parent",
                                 'shared': "True",
                                 }
        if object_with_min_max.min is not None:
            constraints_el.get_or_create('constraint',
                                         assign_id=True,
                                         attrib={'type': 'min',
                                                 'value': object_with_min_max.min,
                                                 } | constraint_attributes,
                                         )
        if object_with_min_max.max is not None:
            constraints_el.get_or_create('constraint',
                                         assign_id=True,
                                         attrib={'type': 'max',
                                                 'value': object_with_min_max.max,
                                                 } | constraint_attributes,
                                         )

    def set_info_links(self, target_list: list):
        if len(target_list) == 0:
            return
        info_links = self.get_or_create('infoLinks')

    def set_rules(self, rules_dict: dict):
        if len(rules_dict) == 0:
            return
        rules = self.get_or_create('rules')

    def set_options(self, options: list['OptionGroup']):
        if len(options) == 0:
            return
        option_entries = self.get_or_create('selectionEntryGroups')
