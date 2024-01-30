import json
import os

from settings import default_system, default_data_directory, default_settings
from system.constants import SystemSettingsKeys
from system.game.games_list import get_game
from system.node import Node
from system.node_collection import NodeCollection
from system.system_file import SystemFile, set_namespace_from_file
from util.generate_util import cleanup_file_match_bs_whitespace
from util.log_util import STYLES, print_styled, get_diff

IGNORE_FOR_DUPE_CHECK = ['selectionEntryGroup', 'selectionEntry', 'constraint', 'repeat', 'condition',
                         'characteristicType']


class System:

    def __str__(self):
        return self.system_name

    def __init__(self, system_name: str = default_system, data_directory: str = default_data_directory,
                 settings=None,
                 include_raw=False, raw_import_settings=None):
        print(f"Initializing {system_name}")
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

        self.nodes = NodeCollection([])
        # The goal is to replace the below indexed lists with just filtering this collection
        self.nodes_by_id: dict[str, Node] = {}
        self.nodes_by_type: dict[str, list[Node]] = {}
        self.nodes_by_name: dict[str, list[Node]] = {}  # can use nodes by name
        self.nodes_by_target_id: dict[str, list[Node]] = {}

        # profileType name: {characteristicType name: typeId}
        self.profile_characteristics: dict[str: dict[str: str]] = {}

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
        for file in self.files:
            self.nodes = self.nodes + file.nodes
            self.nodes_by_id.update(file.nodes_by_id)

            for tag, nodes in file.nodes_by_type.items():
                if tag not in self.nodes_by_type.keys():
                    self.nodes_by_type[tag] = []
                for node in nodes:
                    self.nodes_by_type[tag].append(node)
            for name, nodes in file.nodes_by_name.items():

                if name not in self.nodes_by_name.keys():
                    self.nodes_by_name[name] = []
                self.nodes_by_name[name].extend(nodes)

            for target_id, nodes in file.nodes_by_target_id.items():
                if target_id not in self.nodes_by_target_id.keys():
                    self.nodes_by_target_id[target_id] = []
                self.nodes_by_target_id[target_id].extend(nodes)

        self.define_profile_characteristics()

        self.raw_files = {}
        if include_raw:
            self.init_raw_game(raw_import_settings)

    def define_profile_characteristics(self):
        for node in self.nodes_by_type['profileType']:
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

        json_config = self.read_books_json_config()
        i = 1
        for file_name in books_to_read:
            pub_id = os.path.splitext(file_name)[0]
            filepath = os.path.join(self.game_system_location, 'raw', file_name)
            print('\r', end="")
            print(f"Reading book ({i}/{len(books_to_read)}): {filepath}", end="")
            # Assumes that each raw file is either named as a bs unique ID corresponding to a publication,
            # Or has a publication defined in book_json_config
            book_json_config = {}
            for book in [book for book in json_config if book['file_name'] == file_name]:
                pub_id = book['pub_id']
                book_json_config = book
                break  # Should only be one
            self.raw_files[pub_id] = Book(filepath, self, settings=raw_import_settings, book_config=book_json_config)
            i += 1
        print()
        export_dict = {}
        actions_to_take = raw_import_settings.get(ReadSettingsKeys.ACTIONS, [])

        for pub_id, book in self.raw_files.items():
            export_dict[pub_id] = {}

            skip_non_dump_actions = False
            sys_file_for_pub = self.gst
            publication_node = self.nodes_by_id.get(pub_id)
            if not publication_node:
                print(f"Please create a publication with ID {pub_id},"
                      f" or rename that file to be an existing publication ID")
                skip_non_dump_actions = True
            else:
                print_styled(publication_node.name, STYLES.CYAN)
                sys_file_for_pub = publication_node.system_file
            if skip_non_dump_actions:
                actions_to_take = [Actions.DUMP_TO_JSON] if Actions.DUMP_TO_JSON in actions_to_take else []
            print("Actions to take: " + ", ".join(actions_to_take))
            for page in book.pages:
                print(f"\t{page.page_number} {str(page.page_type or '')}")
                if Actions.DUMP_TO_JSON in actions_to_take:
                    export_dict[pub_id][page.page_number] = page.serialize()
                if Actions.LOAD_SPECIAL_RULES in actions_to_take:
                    for rule_name, rule_text in page.special_rules_dict.items():
                        print(f"\t\tRule: {rule_name}")
                        self.create_or_update_special_rule(page, pub_id, rule_name, rule_text, sys_file_for_pub)
                if Actions.LOAD_WEAPON_PROFILES in actions_to_take:
                    for weapon in page.weapons:
                        print(f"\t\tWeapon: {weapon.name}")
                        self.create_or_update_profile(page, pub_id, weapon, profile_type="Weapon",
                                                      default_sys_file=sys_file_for_pub)
                if Actions.LOAD_UNITS in actions_to_take:
                    for unit in page.units:
                        print(f"\t\tUnit: {unit.name}")
                        self.create_or_update_unit(page, pub_id, unit,
                                                      default_sys_file=sys_file_for_pub)
        if Actions.DUMP_TO_JSON in actions_to_take:
            with open(os.path.join(self.game_system_location, 'raw', "processed.json"), "w",
                      encoding='utf-8') as outfile:
                outfile.write(json.dumps(export_dict, ensure_ascii=False, indent=2))

    def create_or_update_special_rule(self, page, pub_id, rule_name, rule_text, default_sys_file):
        # First look for existing special rules
        node_type = self.settings.get(SystemSettingsKeys.SPECIAL_RULE_TYPE)
        if node_type is None:
            raise Exception("Special rule type is not defined for system")

        nodes = self.nodes.filter(lambda node: (
                node.get_type() == node_type
                and (node.name and node.name.lower() == rule_name.lower())
        ))
        if len(nodes) > 0:
            if len(nodes) > 1:
                nodes_str = ", ".join([str(node) for node in nodes])
                print_styled(f"\t\t\tRule exists multiple times in data files: {nodes_str}", STYLES.RED)
                return
            node = nodes[0]
            print(f"\t\t\tRule exists in data files: {node.id}")
            node.update_attributes({'page': str(page.page_number), 'publicationId': pub_id})
            existing_rule_text = node.get_rules_text()
            diff = get_diff(existing_rule_text, rule_text, 3)
            if diff:
                print_styled("\t\t\tText Differs!", STYLES.PURPLE)
                print(diff)
                node.set_rules_text(rule_name, rule_text)
            return

        # Then create any we couldn't find
        pass

    def create_or_update_profile(self, page, pub_id, raw_profile, profile_type, default_sys_file):
        # A profile should also be in a selection entry with special rules,
        # so once we find the profile, we'll want to find selection entries for it.

        nodes = self.nodes.filter(lambda node: (
                node.get_type() == f"profile:{profile_type}"
                and (node.name and node.name.lower() == raw_profile.name.lower())
        ))
        if len(nodes) > 0:
            if len(nodes) > 1:
                nodes_str = ", ".join([str(node) for node in nodes])
                print_styled(f"\t\t\tProfile exists multiple times in data files: {nodes_str}", STYLES.RED)
                return
            node = nodes[0]
            print(f"\t\t\tProfile exists in data files: {node.id}")
            node.update_attributes({'page': str(page.page_number), 'publicationId': pub_id})
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

    def create_or_update_unit(self, page, pub_id, raw_unit, default_sys_file):

        nodes = self.nodes.filter(lambda node: (
                node.get_type() == f"selectionEntry:unit"
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

            return
        # Then create any we couldn't find

        pass

    def get_duplicates(self) -> dict[str, list['Node']]:

        nodes_with_duplicates = {}
        for name, nodes in self.nodes_by_name.items():
            by_tag = {}
            if len(nodes) > 1:
                for node in nodes:
                    if node.tag not in by_tag.keys():
                        by_tag[node.tag] = []
                    by_tag[node.tag].append(node)
                for tag, tag_nodes in by_tag.items():
                    if tag in IGNORE_FOR_DUPE_CHECK or tag.endswith('Link'):
                        continue
                    if len(tag_nodes) > 1:
                        nodes_with_duplicates[f"{name} - {tag}"] = tag_nodes
        return nodes_with_duplicates

    def save_system(self):
        print(f"Saving {self.system_name}")
        count = len(self.files)
        i = 0
        for system_file in self.files:
            i += 1
            print('\r', end="")
            print(f"Saving file ({i}/{count}): {system_file.path}", end="")
            set_namespace_from_file(system_file.path)
            # utf-8 to keep special characters un-escaped.
            system_file.source_tree.write(system_file.path, encoding="utf-8")
            cleanup_file_match_bs_whitespace(system_file.path)
        print()  # newline to clean up
