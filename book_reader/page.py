from bs4 import BeautifulSoup, Tag

from book_reader.constants import ReadSettingsKeys
from book_reader.raw_entry import RawEntry
from util.log_util import print_styled, STYLES


class Page:
    def __init__(self, book, page_item, settings: {str: bool} = None):
        if settings is None:
            settings = {}
        self.book = book
        self.special_rules_text: dict[str: str] = {}

        page_name = page_item.get_name()
        try:
            page_name_components = page_name.split('.xhtml')[0].split("-")
            try:
                page_range_start = int(page_name_components[0])
            except ValueError:
                page_range_start = int(page_name_components[0].split('_')[0])

            page_number = int(page_range_start) + int(page_name_components[-1]) - 1
        except ValueError:
            # print(f"Could not get page number for {page_name}")
            return

        self.page_number = page_number
        content = page_item.get_content()
        soup = BeautifulSoup(content)
        special_rules_elements_by_name: dict[str: Tag] = {}

        first_paragraph_is_flavor = (ReadSettingsKeys.FIRST_PARAGRAPH_IS_FLAVOR in settings.keys()
                                     and settings[ReadSettingsKeys.FIRST_PARAGRAPH_IS_FLAVOR])

        # Find all special rules elements in the text
        for sr_element in soup.find_all('p', {'class': 'Headers_H4'}):
            special_rule_name = sr_element.get_text().strip()
            if "..." in special_rule_name or not special_rule_name:
                continue  # not actually a special rule
            special_rules_elements_by_name[special_rule_name] = sr_element

        # for each element, find the text between it and the next element
        for special_rule_name, sr_element in special_rules_elements_by_name.items():
            next_paragraph = sr_element.findNext('p')
            if first_paragraph_is_flavor:  # Skip the first paragraph
                next_paragraph = next_paragraph.findNext('p')
            composed_text = ""
            while next_paragraph is not None:

                paragraph_text = next_paragraph.get_text().strip()
                if paragraph_text in special_rules_elements_by_name.keys() or not (
                        next_paragraph['class'][0] in ['Body-Black_Body-Italic',
                                                       'Body-Black_Body-',
                                                       'Body-Black_Bullets',
                                                       ]) or paragraph_text.startswith(
                    'On this page you will find a full description for each of the army special rules used by models drawn from the'):
                    # We've reached the end of this special rule and are on to the next one.
                    # Or a section with different formatting
                    break
                composed_text += paragraph_text + "\n"  # otherwise, add to the rules text
                next_paragraph = next_paragraph.findNext('p')

            composed_text = composed_text.strip()
            if composed_text == "":
                continue  # Not actually a special rule or not a special rule with content
            self.special_rules_text[special_rule_name] = composed_text

        self.weapons: list[RawEntry] = []

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
            stats_headers = stats_headers[-3:]  # Special handling for Brace of Pistols on page 217 of TOW rules
            # TODO: pull out text before stats_headers and prepend it to each weapon name

            # Then, go through all rows in the table
            if not special_rules_left_align:
                continue  # This table doesn't have a special rules indicator, so it's not useful
            next_paragraph = weapon_table

            table_lines: list[tuple[list, list]] = []

            while next_paragraph is not None:
                next_paragraph = next_paragraph.findNext('p')
                if next_paragraph is None or next_paragraph['class'][0] not in ['Stats_Weapon-Stats_Weapon-Body', ]:
                    break

                weapon_name_and_stats_components = []
                weapon_special_rules_components = []
                in_special_rules = False
                for span in next_paragraph.findChildren():
                    span_positioning = span['style'].split('left:')[1].split(';')[0]
                    if span_positioning == special_rules_left_align:
                        in_special_rules = True
                    text = span.text.strip()
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
                weapon_name = " ".join(weapon_name_and_stats_components[0:-3])
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

                self.weapons.append(RawEntry(name=weapon_name, stats=stats_dict, special_rules=special_rules))
