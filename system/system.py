import os

from book_reader.book import Book
from book_reader.constants import ReadSettingsKeys, Actions
from settings import default_system, default_data_directory, default_settings
from system.constants import SystemSettingsKeys
from system.node import Node
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
        if settings is None:
            settings = default_settings
        self.settings = settings
        self.gst = None
        self.files: [SystemFile] = []
        self.nodes_by_id: dict[str, Node] = {}
        self.nodes_by_type: dict[str, list[Node]] = {}
        self.nodes_by_name: dict[str, list[Node]] = {}  # can use nodes by name
        self.nodes_by_target_id: dict[str, list[Node]] = {}

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
        self.raw_files = {}
        if include_raw:
            self.init_raw_game(raw_import_settings)

    def init_raw_game(self, raw_import_settings):
        books_to_read = []
        for file_name in os.listdir(os.path.join(self.game_system_location, 'raw')):
            filepath = os.path.join(self.game_system_location, 'raw', file_name)
            if os.path.isdir(filepath) or os.path.splitext(file_name)[1] not in ['.epub']:
                continue  # Skip this iteration
            books_to_read.append(file_name)
        i = 1
        for file_name in books_to_read:
            pub_id = os.path.splitext(file_name)[0]
            filepath = os.path.join(self.game_system_location, 'raw', file_name)
            print('\r', end="")
            print(f"Reading book ({i}/{len(books_to_read)}): {filepath}", end="")
            # Assumes that each raw file is renamed as a bs unique ID corresponding to a publication.
            self.raw_files[pub_id] = Book(filepath, settings=raw_import_settings, system=self)
            i += 1
        print()
        for pub_id, book in self.raw_files.items():
            publication_node = self.nodes_by_id.get(pub_id)
            if not publication_node:
                print(f"Please create a publication with ID {pub_id},"
                      f" or rename that file to be an existing publication ID")
                exit()
            print_styled(publication_node.name, STYLES.CYAN)
            sys_file_for_pub = publication_node.system_file
            actions_to_take = raw_import_settings.get(ReadSettingsKeys.ACTIONS, [])
            print("Actions to take: " + ", ".join(actions_to_take))
            for page in book.pages:
                print(f"\t{page.page_number}")
                if Actions.LOAD_SPECIAL_RULES in actions_to_take:
                    for rule_name, rule_text in page.special_rules_text.items():
                        print(f"\t\tRule: {rule_name}")
                        self.create_or_update_special_rule(page, pub_id, rule_name, rule_text, sys_file_for_pub)
                if Actions.LOAD_WEAPON_PROFILES in actions_to_take:
                    for weapon in page.weapons:
                        print(f"\t\tWeapon: {weapon.name}")
                        self.create_or_update_profile(page, pub_id, weapon, type="profile:Weapon",
                                                      default_sys_file=sys_file_for_pub)

    def create_or_update_special_rule(self, page, pub_id, rule_name, rule_text, default_sys_file):
        # First look for existing special rules
        nodes = [node for node in self.nodes_by_name.get(rule_name, []) if
                 node.get_type() == self.settings[SystemSettingsKeys.SPECIAL_RULE_TYPE]]
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
                node.set_rules_text(rule_text)
            return
        # Then create any we couldn't find
        for node in (default_sys_file.nodes_by_type[self.settings[SystemSettingsKeys.SPECIAL_RULE_TYPE]]):
            pass

    def create_or_update_profile(self, page, pub_id, raw_profile, type, default_sys_file):
        # A profile should also be in a selection entry with special rules,
        # so once we find the profile, we'll want to find selection entries for it.

        nodes = [node for node in self.nodes_by_name.get(raw_profile.name, []) if
                 node.get_type() == type]
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
                # node.set_profile(stats=)
            return
        # Then create any we couldn't find
        for node in (default_sys_file.nodes_by_type[self.settings[SystemSettingsKeys.SPECIAL_RULE_TYPE]]):
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
