from book_reader.raw_entry import OptionGroup, RawUnit
from util.element_util import get_or_create_sub_element


class SystemElement:
    def __init__(self, system, element):
        self.system = system
        self.element = element

    @property
    def category_book_to_full_name_map(self):
        return self.system.game.category_book_to_full_name_map

    def get_or_create(self, tag, attrib: dict[str:str] = None, assign_id: bool = False):
        return self.system.element_as_system_element(get_or_create_sub_element(self.element, tag, attrib, assign_id))

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
                                                         'name': category_name,
                                                         # Won't actually be the real name, need update script
                                                         'primary': 'true',
                                                         },
                                                 assign_id=True)

    def set_models(self, raw_unit: 'RawUnit'):
        if len(raw_unit.model_profiles) == 0:
            return
        selection_entries = self.get_or_create('selectionEntries')

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
