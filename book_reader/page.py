import re
from typing import TYPE_CHECKING

from bs4 import BeautifulSoup, Tag

if TYPE_CHECKING:
    from book_reader.book import Book
    from system.system_file import SystemFile

from book_reader.constants import ReadSettingsKeys
from book_reader.raw_entry import RawProfile, RawUnit
from util.log_util import print_styled, STYLES


class Page:
    """
    A page's goal is to take something from a book, and turn it into json that we can either export,
     or apply to the game system.
    """

    def __init__(self, book: 'Book', page_number: int):
        self.book = book
        self.page_number = page_number

        config = self.book.page_configs.get(self.page_number, {})
        self.page_type = config.get('type')
        self.target_system_file: 'SystemFile' = config.get('target_system_file')

        self.special_rules_dict: dict[str: str] = {}
        self.wargear_dict: dict[str: str] = {}
        self.types_and_subtypes_dict: dict[str: str] = {}
        self.weapons: list[RawProfile] = []
        self.units_text: list[str] = []
        self.units: list[RawUnit] = []
        self.special_rules_text = None
        self.flavor_text_col = None

    @property
    def settings(self) -> dict[ReadSettingsKeys: str | dict]:
        return self.book.settings

    def serialize(self):
        dict_to_serialize = {'page_type': self.page_type, }
        if self.units:
            dict_to_serialize['Units'] = [unit.serialize() for unit in self.units]
        if self.special_rules_dict:
            dict_to_serialize['Special Rules'] = self.special_rules_dict
        if self.wargear_dict:
            dict_to_serialize['Wargear'] = self.wargear_dict
        if self.types_and_subtypes_dict:
            dict_to_serialize['Types and Subtypes'] = self.types_and_subtypes_dict
        if self.weapons:
            dict_to_serialize['Weapons'] = [profile.serialize() for profile in self.weapons]
        return dict_to_serialize


class EpubPage(Page):
    def __init__(self, book, page_item):
        page_name = page_item.get_name()
        try:
            page_name_components = page_name.split('.xhtml')[0].split("-")
            try:
                page_range_start = int(page_name_components[0])
            except ValueError:
                page_start_components = page_name_components[0].split('_')
                if "Journal" in page_start_components:
                    # Journals are in groups of 28 pages for some reason. So far it's consistent.
                    page_range_start = (int(page_start_components[-2]) - 1) * 28
                else:
                    page_range_start = int(page_start_components[0])
            # Minus one for the cover page:
            page_number = int(page_range_start) + int(page_name_components[-1]) - 1
        except ValueError:
            # print(f"Could not get page number for {page_name}")
            return
        super().__init__(book, page_number)
        content = page_item.get_content()
        soup = BeautifulSoup(content, "html.parser")
        special_rules_elements_by_name: dict[str: Tag] = {}
        table_label_elements: dict[str: Tag] = {}

        first_paragraph_is_flavor = (ReadSettingsKeys.FIRST_PARAGRAPH_IS_FLAVOR in self.settings.keys()
                                     and self.settings[ReadSettingsKeys.FIRST_PARAGRAPH_IS_FLAVOR])

        # Find all special rules elements in the text
        for sr_element in soup.find_all('p', {'class': 'Headers_H4'}):
            special_rule_name = sr_element.get_text().strip()
            if "..." in special_rule_name or not special_rule_name:
                continue  # not actually a special rule
            if " Table" in special_rule_name:
                table_label_elements[special_rule_name] = sr_element
                continue  # Not added to the special rules list.
            special_rules_elements_by_name[special_rule_name] = sr_element

        # for each element, find the text between it and the next element
        for special_rule_name, sr_element in special_rules_elements_by_name.items():
            next_paragraph = sr_element.findNext('p')
            if first_paragraph_is_flavor:  # Skip the first paragraph
                next_paragraph = next_paragraph.findNext('p')
            composed_text = ""
            ends_in_table = False
            while next_paragraph is not None:

                paragraph_text = next_paragraph.get_text().strip()
                paragraph_text = re.sub(r" ", " ", paragraph_text)  # Pull out nbsp

                # This special rule could end in a table. If it does, we'll start parsing it instead of paragraphs.
                if paragraph_text in table_label_elements:
                    ends_in_table = True  # This flag tells us to start processing the table.
                    # Table processing will start at the header

                if (paragraph_text in special_rules_elements_by_name.keys() or not (
                        next_paragraph['class'][0] in ['Body-Black_Body-Italic',
                                                       'Body-Black_Body-',
                                                       'Body-Black_Bullets',
                                                       ])
                        or paragraph_text.startswith('On this page you will find a full description')
                        or paragraph_text.startswith("On the following pages you will find a full description")):
                    # We've reached the end of this special rule and are on to the next one.
                    # Or a section with different formatting
                    break
                composed_text += paragraph_text + "\n"  # otherwise, add to the rules text
                next_paragraph = next_paragraph.findNext('p')

            if ends_in_table:
                composed_text += self.extract_table(next_paragraph)

            composed_text = composed_text.strip()
            if composed_text == "":
                continue  # Not actually a special rule or not a special rule with content
            self.special_rules_dict[special_rule_name] = composed_text

        # KNOWN INPUT ISSUE, Two/additional hand weapon is just missing a name on page 213
        for weapon_table in soup.find_all('p', {'class': 'Stats_Weapon-Stats_Weapon-Header'}):
            # First, see what information we can gather from the header
            # With this method, we can consistently get the start of the special rules column (but nothing else)
            stats_headers = []
            special_rules_left_align = None
            for span in weapon_table.findChildren():
                span_positioning = span['style'].split('left:')[1].split(';')[0]
                header = span.text.strip()
                if header == "Special":
                    special_rules_left_align = span_positioning
                    break
                if header != "":
                    stats_headers.append(header)

            # Pull out text before stats_headers and prepend it to each weapon name
            # This is for weapons that have multiple profiles in the old world
            prepend_to_name = ""
            if len(stats_headers) > 3:
                prepend_to_name = " ".join(stats_headers[:-3]) + " - "

            stats_headers = stats_headers[-3:]

            # Then, go through all rows in the table
            if not special_rules_left_align:
                continue  # This table doesn't have a special rules indicator, so it's not useful
            next_paragraph = weapon_table

            table_lines: list[tuple[list, list]] = []
            weapon_note = ""
            while next_paragraph is not None:
                next_paragraph = next_paragraph.findNext('p')
                if next_paragraph is None:
                    break
                if (next_paragraph['class'][0] in ['Body-Black_Body-Italic']
                        and next_paragraph.get_text().startswith("Note")):  # Note: or Notes:
                    weapon_note = re.sub(r" ", " ", next_paragraph.get_text())
                    break
                if next_paragraph['class'][0] not in ['Stats_Weapon-Stats_Weapon-Body', ]:
                    break

                weapon_name_and_stats_components = []
                weapon_special_rules_components = []
                in_special_rules = False
                for span in next_paragraph.findChildren():
                    span_positioning = span['style'].split('left:')[1].split(';')[0]
                    if span_positioning == special_rules_left_align:
                        in_special_rules = True
                    text = span.text.strip()
                    text = re.sub(r" ", " ", text)  # Pull out nbsp

                    if text == "":
                        continue
                    if in_special_rules:
                        weapon_special_rules_components.append(text)
                    else:
                        weapon_name_and_stats_components.append(text)
                table_lines.append((weapon_name_and_stats_components, weapon_special_rules_components))

            # If a line in the table doesn't have stats, it's really just a continuation of the previous line.
            # Handle all partial lines.
            combined_table_lines = []
            prev_index = -1
            for i in range(len(table_lines)):
                weapon_name_and_stats_components, weapon_special_rules_components = table_lines[i]
                # This is a partial line, we need to add it to the line before it.
                if len(weapon_name_and_stats_components) < 3:
                    try:
                        old1, old2 = combined_table_lines[prev_index]
                        new1 = old1[:-3] + weapon_name_and_stats_components + old1[-3:]
                        new2 = old2 + weapon_special_rules_components
                        combined_table_lines[prev_index] = (new1, new2)
                    except IndexError:
                        print_styled("Issue combining lines", STYLES.RED)
                        print(table_lines)
                        print(combined_table_lines)
                        exit()
                    # Don't update the index
                else:
                    combined_table_lines.append((weapon_name_and_stats_components, weapon_special_rules_components))
                    prev_index += 1

            # Processes the combined lines
            for weapon_name_and_stats_components, weapon_special_rules_components in combined_table_lines:
                weapon_name = prepend_to_name + " ".join(weapon_name_and_stats_components[0:-3])
                weapon_stats_array = weapon_name_and_stats_components[-3:]

                if '(' in weapon_name:
                    try:

                        weapon_name = " ".join(weapon_name_and_stats_components[0:-5])
                        weapon_stats_array = [
                            weapon_name_and_stats_components[-5],
                            " ".join(weapon_name_and_stats_components[-4:-2]),
                            " ".join(weapon_name_and_stats_components[-2:]),
                        ]
                    except IndexError:
                        print_styled("Artillery false alarm", STYLES.RED)
                        print(weapon_name)
                        print(stats_headers)
                        print(weapon_stats_array)
                        exit()

                try:
                    stats_dict = {stats_headers[i]: weapon_stats_array[i] for i in range(len(stats_headers))}
                except IndexError:
                    print_styled("Headers don't line up!", STYLES.RED)
                    print(stats_headers)
                    print(weapon_stats_array)
                    exit()

                special_rules_string = " ".join(weapon_special_rules_components)
                special_rules = []
                if "," in special_rules_string:
                    special_rules = special_rules_string.split(',')  # May leave entries with trailing whitespace
                elif special_rules_string != "":  # a single special rule
                    special_rules = [special_rules_string]
                if weapon_note:  # If there are multiple weapons on the same table, they'll get the same note. That's OK
                    if ":" in weapon_note:
                        weapon_note = weapon_note.split(":")[1].strip()
                    stats_dict.update({"Notes": weapon_note})
                self.weapons.append(
                    RawProfile(name=weapon_name, stats=stats_dict, special_rules=special_rules))

    def extract_table(self, table_header_element):
        table_text = table_header_element.text.strip() + ":\n"
        table_line_element = table_header_element.findNext('p')
        results_label_left_align = None

        table_row_count = -1
        die_roll_col_components = []
        results_col_components = []
        while table_line_element is not None:
            if table_line_element['class'][0] not in ['Body-Black_D-Table-Header',
                                                      'Body-Black_D-Table-Body',
                                                      ]:
                break  # We've reached the end of the table now.

            # To consider, parameterize this and share with Weapons profiles, as it does the same thing,
            # just splitting at Special vs Result

            # process each row of the table
            in_result_column = False
            for span in table_line_element.findAll('span'):  # should ignore links and find all descendant spans
                span_positioning = span['style'].split('left:')[1].split(';')[0]
                component_text = span.text.strip()
                if table_line_element['class'][0] == 'Body-Black_D-Table-Header':
                    if component_text == "Result":
                        results_label_left_align = span_positioning
                if span_positioning == results_label_left_align:
                    in_result_column = True
                if not in_result_column:
                    if component_text != "":
                        if len(die_roll_col_components) - 1 == table_row_count:
                            # We're at the start of a new row
                            results_col_components.append([])
                            die_roll_col_components.append([])
                            table_row_count += 1
                        die_roll_col_components[table_row_count].append(component_text)
                else:
                    results_col_components[table_row_count].append(component_text)

            table_line_element = table_line_element.findNext('p')

        # Clean up the table and print it nicely.
        for row in range(len(die_roll_col_components)):
            die_roll_cell = " ".join(die_roll_col_components[row])
            results_roll_cell = " ".join(results_col_components[row])
            table_text += f"● {die_roll_cell}:\t{results_roll_cell}\n"
        table_text = table_text.strip()
        return table_text
