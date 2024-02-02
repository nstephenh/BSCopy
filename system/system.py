import json
import os

from book_reader.raw_entry import RawUnit, RawProfile
from settings import default_system, default_data_directory, default_settings
from system.constants import SystemSettingsKeys
from system.game.games_list import get_game
from system.node import Node
from system.node_collection import NodeCollection
from system.system_file import SystemFile, set_namespace_from_file, read_categories
from util.log_util import STYLES, print_styled, get_diff
from util.text_utils import get_generic_rule_name, remove_plural, check_alt_names

IGNORE_FOR_DUPE_CHECK = ['selectionEntryGroup', 'selectionEntry', 'constraint', 'repeat', 'condition',
                         'characteristicType']


class System:

    def __str__(self):
        return self.system_name

    def __init__(self, system_name: str = default_system, data_directory: str = default_data_directory,
                 settings=None,
                 include_raw=False, raw_import_settings=None):
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

        self.nodes_with_ids = NodeCollection([])

        # profileType name: {characteristicType name: typeId}
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

        self.raw_files = {}
        if include_raw:
            self.init_raw_game(raw_import_settings)

    def refresh_index(self):
        self.rules_by_name = {node.name: node for node in
                              self.nodes_with_ids.filter(lambda node: node.tag == 'rule' and node.shared)}
        self.wargear_by_name = {node.name: node for node in
                                self.nodes_with_ids.filter(lambda node: node.tag == 'selectionEntry' and node.shared)}
        for file in self.files:
            if file.is_gst:
                # TODO: This also needs ported over to the new implementation.
                # And we need to be able to read non-gst unit types
                self.categories = read_categories(file._source_tree)

    def define_profile_characteristics(self):
        for node in self.nodes_with_ids.filter(lambda x: x.type == 'profileType'):
            self.profile_characteristics[node.name] = {}
            for element in node.get_sub_elements_with_tag('characteristicType'):
                self.profile_characteristics[node.name][element.get('name')] = element.get('id')

    def read_books_json_config(self):
        expected_location = os.path.join(self.game_system_location, 'raw', 'books.json')
        if not os.path.isfile(expected_location):
            return {}
        with open(expected_location) as file:
            return json.load(file)

    def init_raw_game(self, raw_import_settings):
        from book_reader.book import Book
        from book_reader.constants import ReadSettingsKeys, Actions
        books_to_read = []
        for file_name in os.listdir(os.path.join(self.game_system_location, 'raw')):
            filepath = os.path.join(self.game_system_location, 'raw', file_name)
            if os.path.isdir(filepath) or os.path.splitext(file_name)[1] not in ['.epub', '.pdf']:
                continue  # Skip this iteration
            books_to_read.append(file_name)

        name_to_pub_id = {}

        json_config = self.read_books_json_config()
        i = 1
        for file_name in books_to_read:
            file_no_ext = os.path.splitext(file_name)[0]
            filepath = os.path.join(self.game_system_location, 'raw', file_name)
            print('\r', end="")
            print(f"Reading book ({i}/{len(books_to_read)}): {filepath}", end="")
            # Assumes that each raw file is either named as a bs unique ID corresponding to a publication,
            # Or has a publication defined in book_json_config
            book_json_config = {}
            pub_id = None
            name_to_pub_id[file_no_ext] = file_no_ext
            for book in [book for book in json_config if book['file_name'] == file_name]:
                name_to_pub_id[file_no_ext] = book['pub_id']
                pub_id = book['pub_id']
                book_json_config = book
                break  # Should only be one
            self.raw_files[file_no_ext] = Book(filepath, self, settings=raw_import_settings,
                                               book_config=book_json_config, pub_id=pub_id)
            i += 1
        export_dict = {}
        actions_to_take = raw_import_settings.get(ReadSettingsKeys.ACTIONS, [])
        for file_name, book in self.raw_files.items():
            export_dict[file_name] = {}
            pub_id = name_to_pub_id[file_name]
            skip_non_dump_actions = False
            sys_file_for_pub = self.gst
            publication_node = self.nodes_with_ids.get(lambda node: (
                    node.id == pub_id
            ))
            if not publication_node:
                print(f"Please create a publication for {file_name} and define it in books.json,"
                      f" or rename that file to be a publication ID")
                skip_non_dump_actions = True
            else:
                export_dict[file_name]['pub_id'] = pub_id
                print_styled(publication_node.name, STYLES.CYAN)
                sys_file_for_pub = publication_node.system_file
            if skip_non_dump_actions:
                actions_to_take = [Actions.DUMP_TO_JSON] if Actions.DUMP_TO_JSON in actions_to_take else []
            print("Actions to take: " + ", ".join(actions_to_take))
            for page in book.pages:
                print(f"\t{page.page_number} {str(page.page_type or '')}")
                if Actions.DUMP_TO_JSON in actions_to_take:
                    export_dict[file_name][page.page_number] = page.serialize()
                if Actions.LOAD_SPECIAL_RULES in actions_to_take and not page.units:
                    for rule_name, rule_text in page.special_rules_dict.items():
                        print(f"\t\tRule: {rule_name}")
                        self.create_or_update_special_rule(page, rule_name, rule_text, sys_file_for_pub)
                if Actions.LOAD_WEAPON_PROFILES in actions_to_take and not page.units:
                    for weapon in page.weapons:
                        print(f"\t\tWeapon: {weapon.name}")
                        self.create_or_update_profile(page, weapon, profile_type="Weapon",
                                                      default_sys_file=sys_file_for_pub)
                if Actions.LOAD_UNITS in actions_to_take:
                    for unit in page.units:
                        print(f"\t\tUnit: {unit.name}")
                        self.create_or_update_unit(unit,
                                                   default_sys_file=sys_file_for_pub)
        if Actions.DUMP_TO_JSON in actions_to_take:
            with open(os.path.join(self.game_system_location, 'raw', "processed.json"), "w",
                      encoding='utf-8') as outfile:
                outfile.write(json.dumps(export_dict, ensure_ascii=False, indent=2))

    def create_or_update_special_rule(self, page, rule_name, rule_text, default_sys_file):
        # First look for existing special rules
        node_type = self.settings.get(SystemSettingsKeys.SPECIAL_RULE_TYPE)
        if node_type is None:
            raise Exception("Special rule type is not defined for system")

        nodes = self.nodes_with_ids.filter(lambda node: (
                node.type == node_type
                and (node.name and node.name.lower() == rule_name.lower())
        ))
        if len(nodes) > 0:
            if len(nodes) > 1:
                nodes_str = ", ".join([str(node) for node in nodes])
                print_styled(f"\t\t\tRule exists multiple times in data files: {nodes_str}", STYLES.RED)
                return
            node = nodes[0]
            print(f"\t\t\tRule exists in data files: {node.id}")
            node.update_pub_and_page(page)
            existing_rule_text = node.get_rules_text()
            diff = get_diff(existing_rule_text, rule_text, 3)
            if diff:
                print_styled("\t\t\tText Differs!", STYLES.PURPLE)
                print(diff)
                node.set_rules_text(rule_name, rule_text)
            return

        # Then create any we couldn't find
        rule_node = default_sys_file.create_shared_node('rule', attrib={
            'name': rule_name
        })
        rule_node.update_pub_and_page(page)

    def get_rule_name_and_id(self, rule_name: str) -> (str, str) or (None, None):
        rule_name = rule_name.strip()
        rule_name = get_generic_rule_name(rule_name)
        if rule_name in self.rules_by_name:
            return rule_name, self.rules_by_name[rule_name].id
        rule_name = get_generic_rule_name(rule_name, True)
        if rule_name in self.rules_by_name:
            return rule_name, self.rules_by_name[rule_name].id
        print(f"Could not find rule: {rule_name}")
        self.errors.append(f"Could not find rule: {rule_name}")
        return None, None

    def get_wargear_name_and_id(self, wargear_name: str) -> (str, str) or (None, None):
        lookup_name = check_alt_names(wargear_name)
        if "Two" in lookup_name:
            lookup_name = lookup_name.split("Two")[1].strip()
            lookup_name = remove_plural(lookup_name)
        if "Mounted" in lookup_name:
            lookup_name = lookup_name.split("Mounted")[1].strip()

        if lookup_name in self.wargear_by_name:
            return lookup_name, self.wargear_by_name[lookup_name].id
        self.errors.append(f"Could not find wargear for: {wargear_name}")
        if lookup_name != wargear_name:
            self.errors.append(f"\t Checked under {lookup_name}")
        return None, None

    def get_profile_type_id(self, profile_type: str):
        return self.nodes_with_ids.filter(lambda node: (
                node.type == f"profileType"
                and (node.name == profile_type)))[0].id

    def get_characteristic_name_and_id(self, profile_type: str, characteristic_name: str):
        characteristic_list = self.game.WEAPON_PROFILE_TABLE_HEADERS
        full_characteristic_list = self.game.WEAPON_PROFILE_TABLE_HEADERS
        if profile_type == 'Unit':
            characteristic_list = self.game.UNIT_PROFILE_TABLE_HEADERS
            full_characteristic_list = self.game.UNIT_PROFILE_TABLE_HEADERS_FULL
        elif profile_type == self.game.ALT_PROFILE_NAME:
            characteristic_list = self.game.ALT_UNIT_PROFILE_TABLE_HEADERS
            full_characteristic_list = self.game.ALT_UNIT_PROFILE_TABLE_HEADERS_FULL

        full_name = characteristic_name
        if characteristic_name in characteristic_list:
            i = characteristic_list.index(characteristic_name)
            full_name = full_characteristic_list[i]
        if full_name not in self.profile_characteristics[profile_type]:
            raise ValueError(f"'{full_name}' is not a valid characteristic in the game system")
        return full_name, self.profile_characteristics[profile_type][full_name]

    def create_or_update_profile(self, page, raw_profile: 'RawProfile', profile_type, default_sys_file):
        # A profile should also be in a selection entry with special rules,
        # so once we find the profile, we'll want to find selection entries for it.

        nodes = self.nodes_with_ids.filter(lambda node: (
                node.type == f"profile:{profile_type}"
                and (node.name and node.name.lower() == raw_profile.name.lower())
        ))
        if len(nodes) > 0:
            if len(nodes) > 1:
                nodes_str = ", ".join([str(node) for node in nodes])
                print_styled(f"\t\t\tProfile exists multiple times in data files: {nodes_str}", STYLES.RED)
                return
            node = nodes[0]
            print(f"\t\t\tProfile exists in data files: {node.id}")
            node.update_pub_and_page(page)
            existing_profile_text = node.get_diffable_profile()
            new_profile_text = raw_profile.get_diffable_profile()
            diff = get_diff(existing_profile_text, new_profile_text, 3)
            if diff:
                print_styled("\t\t\tText Differs!", STYLES.PURPLE)
                print(diff)
                node.set_profile(raw_profile, profile_type)
            return
        # Then create any we couldn't find
        pass

    def create_or_update_unit(self, raw_unit: 'RawUnit', default_sys_file: 'SystemFile'):
        node = self.get_or_create_unit(raw_unit, default_sys_file)
        if node is None:
            return

        node.update_pub_and_page(raw_unit.page)
        node.set_force_org(raw_unit)

        node.set_models(raw_unit)
        node.set_options(raw_unit.unit_options)
        node.set_rule_info_links(raw_unit.special_rules)
        node.set_rules(raw_unit.special_rule_descriptions)

    def get_or_create_unit(self, raw_unit, default_sys_file: 'SystemFile'):
        raw_unit.name = raw_unit.name.title()

        nodes = self.nodes_with_ids.filter(lambda node: (
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
            print(f"\t\t\tUnit exists in data files: {node.id}")
            return node

        # Then create any we couldn't find
        if not default_sys_file:
            print_styled("\t\t\tCannot create a unit without a file to create them in")
            return

        print_styled(f"\t\t\tCreating unit in {default_sys_file.name}", STYLES.GREEN)
        return default_sys_file.create_shared_node('selectionEntry',
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
