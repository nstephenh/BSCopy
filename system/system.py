import datetime
import json
import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from book_reader.page import Page

from book_reader.raw_entry import RawUnit, RawProfile
from settings import default_system, default_data_directory, default_settings
from system.constants import SystemSettingsKeys
from system.game.games_list import get_game
from system.node import Node
from system.node_collection import NodeCollection
from system.system_file import SystemFile, set_namespace_from_file
from util.log_util import STYLES, print_styled
from util.text_utils import get_generic_rule_name, remove_plural, check_alt_names

IGNORE_FOR_DUPE_CHECK = ['selectionEntryGroup', 'selectionEntry', 'constraint', 'repeat', 'condition',
                         'characteristicType', 'modifier']


class System:

    def __str__(self):
        return self.system_name

    def __init__(self, system_name: str = default_system, data_directory: str = default_data_directory,
                 settings=None,
                 include_raw=False, raw_import_settings=None):

        self.run_timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M")
        print(f"Initializing {system_name}")
        self.errors = []
        print(settings)
        if settings is None:
            settings = {}
        self.game = get_game(system_name, settings.get(SystemSettingsKeys.GAME_IMPORT_SPEC))
        self.settings = dict(default_settings)
        if self.game:
            self.settings.update(self.game.default_settings)
        self.settings.update(settings)

        self.gst = None
        self.files: [SystemFile] = []

        self.all_nodes = NodeCollection([])
        self.nodes_with_ids = NodeCollection([])

        # profileType name: {characteristicType name: typeId}
        self.profile_types: dict[str: str] = {}
        self.profile_characteristics: dict[str: dict[str: str]] = {}

        self.categories: dict[str: str] = {}

        self.system_name = system_name
        self.game_system_location = os.path.join(data_directory, system_name)
        game_files = os.listdir(self.game_system_location)
        temp_file_list = []  # List so we can get a count for progress bar
        for file_name in game_files:
            filepath = os.path.join(self.game_system_location, file_name)
            if os.path.isdir(filepath) or os.path.splitext(file_name)[1] not in ['.cat', '.gst']:
                continue  # Skip this iteration
            temp_file_list.append(filepath)
        count = len(temp_file_list)
        i = 0
        for filepath in temp_file_list:
            i += 1
            print('\r', end="")
            print(f"Loading file ({i}/{count}): {filepath}", end="")
            file = SystemFile(self, filepath)
            self.files.append(file)
            if file.is_gst:
                self.gst = file
        print()  # Newline after progress bar

        self.define_profile_characteristics()  # These should not be updated during a session, so it's OK to index them.

        self.wargear_by_name = {}
        self.rules_by_name = {}
        self.categories = {}
        self.refresh_index()

        self.raw_pub_priority = {}
        self.raw_files = {}
        if include_raw:
            self.init_raw_game(raw_import_settings)

    def refresh_index(self):
        self.rules_by_name = {node.name.lower(): node for node in
                              self.nodes_with_ids.filter(lambda node: node.tag == 'rule' and node.shared)}
        self.wargear_by_name = {node.name.lower(): node for node in
                                self.nodes_with_ids.filter(lambda node: node.tag == 'selectionEntry'
                                                                        and node.shared
                                                                        and not node.collective)}
        categories = {node.name: node for node in
                      self.nodes_with_ids.filter(lambda node: node.tag == 'categoryEntry')}
        for name, category in categories.items():
            name = name.strip()
            if name.endswith(":"):
                name = name[:-1]
            if name.lower().endswith(" sub-type"):
                name = name[:-len(" sub-type")]
                if name.lower().endswith(" unit"):
                    name = name[:-len(" unit")]
            elif name.lower().endswith(" unit type"):
                name = name[:-len(" unit type")]
            self.categories[name] = category

    def define_profile_characteristics(self):
        for node in self.nodes_with_ids.filter(lambda x: x.type == 'profileType'):
            self.profile_types[node.name] = node.id
            self.profile_characteristics[node.name] = {}
            for element in node.get_sub_elements_with_tag('characteristicType'):
                self.profile_characteristics[node.name][element.get('name')] = element.get('id')

    def read_books_json_config(self):
        expected_location = os.path.join(self.game_system_location, 'raw', 'books.json')
        if not os.path.isfile(expected_location):
            return {}
        with open(expected_location) as file:
            json_config = json.load(file)
            # read these as we want them for even non-initialized books.
            for book_config in json_config:
                pub_id = book_config.get('pub_id')
                if pub_id:
                    self.raw_pub_priority[pub_id] = book_config.get('priority', 0)
            return json_config

    def init_raw_game(self, raw_import_settings):
        from book_reader.book import Book
        from book_reader.constants import ReadSettingsKeys, Actions
        books_to_read = []
        for file_name in os.listdir(os.path.join(self.game_system_location, 'raw')):
            filepath = os.path.join(self.game_system_location, 'raw', file_name)
            if os.path.isdir(filepath) or os.path.splitext(file_name)[1] not in ['.epub', '.pdf']:
                continue  # Skip this iteration
            books_to_read.append(file_name)

        json_config = self.read_books_json_config()
        i = 1
        for file_name in books_to_read:
            file_no_ext = os.path.splitext(file_name)[0]
            filepath = os.path.join(self.game_system_location, 'raw', file_name)
            print('\r', end="")
            print(f"Reading book ({i}/{len(books_to_read)}): {filepath}", end="")
            # Publication and target file will be defined in book_json_config
            book_json_config = {}
            for book in [book for book in json_config if book['file_name'] == file_name]:
                book_json_config = book
                break  # Should only be one
            self.raw_files[file_no_ext] = Book(filepath, self, settings=raw_import_settings,
                                               book_config=book_json_config)
            i += 1
        export_dict = {}
        self.raw_files = dict(sorted(self.raw_files.items(), key=lambda pair: pair[1].priority, reverse=True))
        all_actions_to_take = raw_import_settings.get(ReadSettingsKeys.ACTIONS, [])
        for file_name, book in self.raw_files.items():
            export_dict[file_name] = {}
            print_styled(file_name, STYLES.CYAN)
            for page in book.pages:
                print(f"\t{page.page_number} {str(page.page_type or '')} targeting {page.target_system_file}")

                actions_to_take = all_actions_to_take
                if not page.target_system_file:
                    actions_to_take = [Actions.DUMP_TO_JSON] if Actions.DUMP_TO_JSON in all_actions_to_take else []

                if Actions.DUMP_TO_JSON in actions_to_take:
                    export_dict[file_name][page.page_number] = page.serialize()
                if Actions.LOAD_SPECIAL_RULES in actions_to_take and not page.units:
                    for rule_name, rule_text in page.special_rules_dict.items():
                        print(f"\t\tRule: {rule_name}")
                        self.create_or_update_special_rule(page, rule_name, rule_text)
                    for unit_type, text in page.types_and_subtypes_dict.items():
                        print(f"\t\tType: {unit_type}")
                        self.create_or_update_category(page, unit_type, text)
                    for unit_type, text in page.wargear_dict.items():
                        print(f"\t\tWargear: {unit_type}")
                        self.create_or_update_wargear(page, unit_type, text)
                if Actions.LOAD_WEAPON_PROFILES in actions_to_take and not page.units:
                    for weapon in page.weapons:
                        print(f"\t\tWeapon: {weapon.name}")
                        self.create_or_update_upgrade(weapon, profile_type="Weapon")
            if Actions.LOAD_UNITS in all_actions_to_take:
                self.refresh_index()  # We need to update the index before loading units
                for page in book.pages:
                    print(f"\t{page.page_number} {str(page.page_type or '')}")
                    for unit in page.units:
                        print(f"\t\tUnit: {unit.name}")
                        if page.target_system_file is None:
                            print_styled(f"\t\tNo target file, skipping",
                                         STYLES.YELLOW)
                            continue
                        self.create_or_update_unit(unit)

        if Actions.DUMP_TO_JSON in all_actions_to_take:
            with open(os.path.join(self.game_system_location, 'raw', "processed.json"), "w",
                      encoding='utf-8') as outfile:
                outfile.write(json.dumps(export_dict, ensure_ascii=False, indent=2))

    def create_or_update_special_rule(self, page: 'Page', rule_name, rule_text):
        # First look for existing special rules
        node_type = self.settings.get(SystemSettingsKeys.SPECIAL_RULE_TYPE)
        if node_type is None:
            raise Exception("Special rule type is not defined for system")

        _, existing_instance_id = self.get_rule_name_and_id(rule_name)
        if existing_instance_id is not None:
            print_styled(f"\t\t\tRule already exists in system: {existing_instance_id}", STYLES.RED)
            return

        # Create the new rule
        print_styled(f"\t\t\tCreating rule in {page.target_system_file}", STYLES.GREEN)

        rule_node = page.target_system_file.get_or_create_shared_node('rule', attrib={
            'name': rule_name
        })
        rule_node.update_pub_and_page(page)
        rule_node.set_rules_text(rule_text)

    def get_rule_name_and_id(self, rule_name: str) -> (str, str) or (None, None):
        rule_name = rule_name.strip()
        rule_name = rule_name.rstrip("*")
        rule_name = get_generic_rule_name(rule_name)
        if rule_name.lower() in self.rules_by_name:
            found_rule = self.rules_by_name[rule_name.lower()]
            return found_rule.name, found_rule.id
        rule_name = get_generic_rule_name(rule_name, True)
        if rule_name.lower() in self.rules_by_name:
            found_rule = self.rules_by_name[rule_name.lower()]
            return found_rule.name, found_rule.id
        return None, None

    def get_wargear_name_and_id(self, wargear_name: str) -> (str, str) or (None, None):
        lookup_name = check_alt_names(wargear_name)
        if "Two" in lookup_name:
            lookup_name = lookup_name.split("Two")[1].strip()
            lookup_name = remove_plural(lookup_name)
        if "Mounted" in lookup_name:
            lookup_name = lookup_name.split("Mounted")[1].strip()
        lookup_name = lookup_name.rstrip("*")
        if lookup_name.lower() in self.wargear_by_name:
            return lookup_name, self.wargear_by_name[lookup_name.lower()].id
        return lookup_name, None

    def get_profile_type_id(self, profile_type: str):
        return self.nodes_with_ids.filter(lambda node: (
                node.type == f"profileType"
                and (node.name == profile_type)))[0].id

    def get_characteristic_name_and_id(self, characteristic_name: str, profile_type: str = None):
        if profile_type is None:
            profile_type = "Weapon"
        full_name = self.game.get_full_characteristic_name(characteristic_name, profile_type)
        if full_name not in self.profile_characteristics[profile_type]:
            raise ValueError(f"'{full_name}' is not a valid characteristic in the game system")
        return full_name, self.profile_characteristics[profile_type][full_name]

    def create_or_update_category(self, page, name, text):
        name = name.title()
        if len(text) == 0:
            print_styled(f"\t\t\tCategory has no text: {name}", STYLES.RED)
            return

        # Then create any we couldn't find
        page.target_system_file.root_node.create_category(name, text, page)

    def create_or_update_wargear(self, page, wargear_name, wargear_text):
        wargear_as_profile = RawProfile(wargear_name, page, {'Description': wargear_text})
        self.create_or_update_upgrade(wargear_as_profile, 'Wargear Item')

    def create_or_update_upgrade(self, upgrade_profile, profile_type):
        node = upgrade_profile.page.target_system_file.get_or_create_shared_node('selectionEntry', attrib={
            'name': upgrade_profile.name,
            'type': 'upgrade',
        })
        node.set_rule_info_links(upgrade_profile)
        node = node.get_or_create_child('profiles')
        node = node.get_or_create_child('profile', attrib={
            'name': upgrade_profile.name,
            'typeName': profile_type,
            'hidden': "false",
            'typeId': self.profile_types[profile_type]
        })
        node.set_profile_characteristics(upgrade_profile, profile_type)

    def create_or_update_unit(self, raw_unit: 'RawUnit'):
        node = self.get_or_create_unit(raw_unit)
        if node is None:  # May be null if there are two instances of the unit in the target file.
            return

        node.update_pub_and_page(raw_unit.page)
        node.set_force_org(raw_unit)
        node.set_cost(raw_unit.points)

        node.set_models(raw_unit)
        node.set_options(raw_unit)
        node.set_rule_info_links(raw_unit)
        node.set_rules(raw_unit)

        for error in raw_unit.errors:
            node.append_error_comment(error, raw_unit.name)

    def get_or_create_unit(self, raw_unit) -> Node or None:
        raw_unit.name = raw_unit.name.title()

        nodes = raw_unit.page.target_system_file.nodes_with_ids.filter(lambda node: (
                node.type == f"selectionEntry:unit"
                and (node.name and node.name.lower() == raw_unit.name.lower())
        ))
        # Find existing units
        if len(nodes) > 0:
            if len(nodes) > 1:
                nodes_str = ", ".join([str(node) for node in nodes])
                print_styled(f"\t\t\tUnit exists multiple times in data files: {nodes_str}", STYLES.RED)
                return
            node = nodes[0]
            print(f"\t\t\tUnit exists in data files: {node}")
            return node

        # Then create any we couldn't find
        print_styled(f"\t\t\tCreating unit in {raw_unit.page.target_system_file.name}", STYLES.GREEN)
        return raw_unit.page.target_system_file.get_or_create_shared_node('selectionEntry',
                                                                          attrib={
                                                                              'name': raw_unit.name,
                                                                              'type': 'unit',
                                                                          })

    def get_duplicates(self) -> dict[str, list['Node']]:
        duplicate_groups = {}
        nodes_to_check = self.nodes_with_ids.filter(lambda x: not (x.tag in IGNORE_FOR_DUPE_CHECK
                                                                   or x.is_link()
                                                                   ))
        number_of_nodes = len(nodes_to_check)
        for i, node in enumerate(nodes_to_check):
            print('\r', end="")
            print(f"Checking node ({i}/{number_of_nodes}): {node}", end="")
            duplicates = nodes_to_check.filter(lambda x: x.tag == node.tag and x.name == node.name)
            if len(duplicates) > 1:
                duplicate_groups[f"{node.name} - {node.tag}"] = duplicates
        print()
        return duplicate_groups

    def try_get_name(self, value):
        node = self.nodes_with_ids.get(lambda x: x.id == value)
        if node:
            return node.generated_name
        return value


    def save_system(self):
        print(f"Saving {self.system_name}")
        count = len(self.files)
        i = 0
        for system_file in self.files:
            i += 1
            print('\r', end="")
            print(f"Saving file ({i}/{count}): {system_file.path}", end="")
            set_namespace_from_file(system_file.path)
            system_file.save()
        print()  # newline to clean up
