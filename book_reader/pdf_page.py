from book_reader.constants import PageTypes
from book_reader.page import Page
from book_reader.raw_entry import RawUnit, RawProfile, RawModel
from system.game.game import Game
from text_to_rules import text_to_rules_dict
from util import text_utils
from util.log_util import STYLES, print_styled
from util.text_utils import split_into_columns, split_at_header, split_after_header


class PdfPage(Page):

    def __init__(self, book, raw_text, page_number, prev_page_type=None):
        super().__init__(book, page_number)
        self.raw_text = text_utils.replace_quote_alikes(raw_text)
        self.page_number = page_number
        if self.page_number and self.raw_text.rstrip().endswith(str(self.page_number)):
            self.raw_text = self.raw_text.rstrip()[:-len(str(self.page_number))]
        if self.raw_text.strip() == "" or len(self.raw_text.strip().splitlines()) < 3:
            self.page_type = PageTypes.BLANK_OR_IGNORED
            return
        if not self.page_type or self.page_type == PageTypes.UNIT_PROFILES:
            self.try_handle_units()

        if int(page_number) == 82:
            print(raw_text)
        if not self.page_type or self.page_type == PageTypes.SPECIAL_RULES:
            self.handle_special_rules_page(prev_page_type)
        if not self.page_type or self.page_type == PageTypes.WEAPON_PROFILES:
            self.handle_weapon_profiles_page(prev_page_type)
        if not self.page_type or self.page_type == PageTypes.WARGEAR:
            self.handle_wargear_page(prev_page_type)
        if not self.page_type or self.page_type == PageTypes.TYPES_AND_SUBTYPES:
            self.handle_types_page(prev_page_type)

        # Pull out any special rules or profiles, either the main body of the page, or set from units.
        self.process_weapon_profiles()
        if self.page_type != PageTypes.WEAPON_PROFILES:  # A weapon page shouldn't have any special rules on it.
            self.process_special_rules()

        for unit in self.units:
            unit.page_weapons = self.weapons
            unit.process_subheadings()
            if unit.errors:
                self.book.system.errors += unit.errors

    def try_handle_units(self):
        if self.book.system.game.ProfileLocator in self.raw_text:
            self.get_text_units()
            for unit in self.units_text:
                self.process_unit(unit)
            if len(self.units):  # if we found any units, this page is a units page
                self.page_type = PageTypes.UNIT_PROFILES

    def handle_special_rules_page(self, prev_page_type):
        # Special rules pages are two-column format
        has_special_rules_header = "Special Rules".lower() in self.raw_text.lower().lstrip().splitlines()[2]
        header_text, col_1, col_2, _ = split_into_columns(self.raw_text, ensure_middle=True, debug_print_level=0)

        # If page doesn't have a special rules header and isn't after a previous special rules page,
        # then it's not a special rules page.
        if not has_special_rules_header and not prev_page_type == PageTypes.SPECIAL_RULES:
            return

        self.page_type = PageTypes.SPECIAL_RULES
        print_styled(f"\tThis is a special rules page", STYLES.CYAN)

        self.special_rules_text = col_1 + "\n" + col_2

    def handle_weapon_profiles_page(self, prev_page_type):
        has_armoury_header = "Armoury".lower() in self.raw_text.lstrip().splitlines()[0].lower()
        if not has_armoury_header and not prev_page_type == PageTypes.WEAPON_PROFILES:
            return
        self.page_type = PageTypes.WEAPON_PROFILES
        self.special_rules_text = self.raw_text

    def handle_wargear_page(self, prev_page_type):
        header_text, col_1, col_2, _ = split_into_columns(self.raw_text, ensure_middle=True, debug_print_level=0)
        first_line = ""
        if header_text.lstrip().splitlines():
            first_line = header_text.lstrip().splitlines()[0].lower()
        has_wargear_header = "Wargear".lower() in first_line and "ADDITIONAL".lower() not in first_line
        if not has_wargear_header and not prev_page_type == PageTypes.WARGEAR:
            return
        self.page_type = PageTypes.WARGEAR
        self.special_rules_text = col_1 + "\n" + col_2

    def handle_types_page(self, prev_page_type):
        has_types_header = "Unit Types".lower() in self.raw_text.lstrip().splitlines()[0].lower()
        if not has_types_header and not prev_page_type == PageTypes.TYPES_AND_SUBTYPES:
            return
        self.page_type = PageTypes.TYPES_AND_SUBTYPES
        self.special_rules_text = self.raw_text

    @property
    def game(self) -> 'Game':
        return self.book.system.game

    def get_number_of_units(self):
        units = 0
        for line in self.raw_text.splitlines():
            if self.does_line_contain_profile_header(line):
                # print(f"Line contains profile header: {line}")
                units += 1
        return units

    def does_line_contain_profile_header(self, line) -> bool:
        if not len(self.game.UNIT_PROFILE_TABLE_HEADERS):
            raise Exception("No UNIT PROFILE HEADERS")
        profile_header_types = [self.game.UNIT_PROFILE_TABLE_HEADERS]
        if len(self.game.ALT_UNIT_PROFILE_TABLE_HEADERS):
            profile_header_types.append(self.game.ALT_UNIT_PROFILE_TABLE_HEADERS)
        for header in profile_header_types:
            if text_utils.does_line_contain_header(line, header):
                return True
        return False

    def get_unit_profile_headers(self, text: str) -> [str]:
        if not len(self.game.UNIT_PROFILE_TABLE_HEADERS):
            raise Exception("No UNIT PROFILE HEADERS")
        profile_header_types = [self.game.UNIT_PROFILE_TABLE_HEADERS]
        if len(self.game.ALT_UNIT_PROFILE_TABLE_HEADERS):
            profile_header_types.append(self.game.ALT_UNIT_PROFILE_TABLE_HEADERS)
        for line in text.splitlines():
            for header in profile_header_types:
                if text_utils.does_line_contain_header(line, header):
                    return header
        return

    def does_contain_stagger(self, headers):
        indexes = []
        active_header_index = 0
        for line in self.raw_text.splitlines():
            if headers[active_header_index] in line:
                indexes.append(line.index(headers[active_header_index]))
                active_header_index += 1
                if active_header_index == len(headers) - 1:
                    break
        if active_header_index != (len(headers) - 1):
            raise Exception(
                "We can't tell if this has stagger because it doesn't have all the headers: " + str(headers))
        alignment = indexes[0]
        for header_alignment in indexes[1:]:
            if header_alignment != alignment:
                return False, 0
        return True, alignment

    def get_text_units(self):

        num_units = self.get_number_of_units()
        if num_units == 0:
            return

        if self.game.COULD_HAVE_STAGGERED_HEADERS:
            print("Could have Stagger!")
            # TODO make this more generic
            header_that_may_be_staggered = None
            for staggered_row_header_option in ["Wargear", "Options", "Unit Composition"]:  # Wargear might not exist
                line_with_wargear_header = text_utils.get_index_of_line_with_headers(self.raw_text,
                                                                                     [staggered_row_header_option])
                if line_with_wargear_header is not None:
                    header_that_may_be_staggered = staggered_row_header_option
                    break

            lines = self.raw_text.splitlines()

            left_sidebar_divider_index = lines[line_with_wargear_header].index(header_that_may_be_staggered)
            if left_sidebar_divider_index:  # Left flavor text
                _, self.flavor_text_col, rules_text, _ = text_utils.split_into_columns_at_divider(self.raw_text,
                                                                                                  left_sidebar_divider_index,
                                                                                                  debug_print_level=0)
            else:  # Right flavor text, column detection should work.
                page_header, rules_text, self.flavor_text_col, _ = \
                    split_into_columns(self.raw_text, debug_print_level=0)
                rules_text = page_header + rules_text

            if "Wargear" in rules_text:
                line_with_wargear_header = text_utils.get_index_of_line_with_headers(rules_text,
                                                                                     ["Wargear"])
            else:  # May not have wargear, may only have special rules
                line_with_wargear_header = text_utils.get_index_of_line_with_headers(rules_text,
                                                                                     ["Special Rules"])
            lines = rules_text.splitlines()

            top_half = "\n".join(lines[:line_with_wargear_header])
            bottom_half = "\n".join(lines[line_with_wargear_header:])

            if left_sidebar_divider_index:
                top_half = text_utils.un_justify(top_half)

            unit_composition_index = text_utils.get_index_of_line_with_headers(top_half,
                                                                               ["Unit Composition", "Unit Type"])
            lines = top_half.splitlines()
            profiles = "\n".join(lines[:unit_composition_index])
            uc_and_ut = "\n".join(lines[unit_composition_index:])

            if left_sidebar_divider_index:
                uc_and_ut = text_utils.un_justify(uc_and_ut)

            ut_index = uc_and_ut.index("Unit Type")

            _, uc, ut, _ = text_utils.split_into_columns_at_divider(uc_and_ut, ut_index,
                                                                    debug_print_level=0)

            rules_text = "".join([profiles, uc, ut, bottom_half])

            if rules_text:
                self.units_text = [self.cleanup_unit_text(rules_text)]
            return
        else:
            page_header, col_1_text, col_2_text, _ = split_into_columns(self.raw_text, debug_print_level=0)

            # If a datasheet, it should have two columns in the center of the page.
            if self.book.system.game.ProfileLocator not in col_1_text and self.book.system.game.ProfileLocator not in col_2_text:
                return False  # Not a datasheet
            rules_text = col_1_text if self.book.system.game.ProfileLocator in col_1_text else col_2_text
            self.flavor_text_col = col_2_text if self.book.system.game.ProfileLocator in col_2_text else col_1_text

            rules_text = page_header + rules_text

        if num_units > 1:  # There may be more than one unit, but there may not be.

            self.units_text = [self.cleanup_unit_text(unit_text) for unit_text in self.find_multiple_units(rules_text)]
            return

        self.units_text = [self.cleanup_unit_text(rules_text)]

    def find_multiple_units(self, rules_text):
        unit_text = [[]]  # 2D array containing lines for each unit.
        unit_counter = 0
        in_table = False  # In table starts when we start a table and ends when we hit troop type,
        # so we get all the "Note" or "Notes" in the table.
        for line in rules_text.splitlines():
            # If we come across a stat block, check the previous lines to see if it was a unit.
            if not in_table and self.does_line_contain_profile_header(line):
                # Check the previous line, it should either be a unit name, or "Note:"
                last_line = ""
                while last_line.strip() == "":
                    last_line = unit_text[unit_counter].pop() + "\n" + last_line  # Preserve empty lines.

                #  If this ended in a colon, it is not the start of a unit, the previous line is
                # "When taken as a character mount, <unit> has the following profile:"
                if not last_line.strip().endswith(":"):
                    # If this is a unit, increment the counter and set us as in a table.
                    in_table = True
                    unit_counter += 1
                    unit_text.append([])
                # Append the line we popped, either to the old entry or the new one.
                unit_text[unit_counter].append(last_line)
                unit_text[unit_counter].append(line)  # and append our newly processed line as we'll skip the loops one.
                continue
            if in_table:
                if self.game.ProfileLocator in line:
                    in_table = False  # The table only ends with "Troop Type:" and not with "Notes" or any other text.

            # Always then append the line we just processed.
            unit_text[unit_counter].append(line)

        # The first entry in unit text should ideally end up being an empty array,
        # as it had the name and then was popped out.
        unit_text = ["\n".join(unit_lines) for unit_lines in unit_text[1:]]
        # for unit in unit_text:
        #     print_styled("Separated Unit:", STYLES.GREEN)
        #     print(unit)
        return unit_text

    def cleanup_unit_text(self, rules_text):
        """
        Take the rules text from the page and clean it up.
        :param rules_text:
        :return:
        """
        profile_locator = self.game.ProfileLocator

        if not self.game.MIDDLE_IN_2_COLUMN:  # This block is for the old world handling,
            if self.game.ENDS_AFTER_SPECIAL_RULES:  # which ends with the special rules section
                rules_text, self.special_rules_text = split_after_header(rules_text, "Special Rules:")
            return rules_text

        upper_half = rules_text
        was_split, profiles, upper_half = split_at_header(profile_locator, upper_half, header_at_end_of_line=False)
        if not was_split:
            print(f"Could not split at {profile_locator}")
            return  # If this datasheet doesn't have Unit composition, something is wrong

        # print_styled("Upper Half", STYLES.GREEN)
        _, upper_half, wargear_and_on = split_at_header("Wargear", upper_half, header_at_end_of_line=False)

        # Find the fist section after special rules
        headers = self.game.UNIT_SUBHEADINGS[self.game.UNIT_SUBHEADINGS.index("Special Rules") + 1:]
        end_of_wargear_sr_bullets = text_utils.get_first_non_list_or_header_line(wargear_and_on, headers)
        lines = wargear_and_on.splitlines()
        if end_of_wargear_sr_bullets:  # Otherwise, there will be no options, access points, dedicated transport, etc
            self.special_rules_text = "\n".join(lines[end_of_wargear_sr_bullets:])
            wargear_and_on = "\n".join(lines[:end_of_wargear_sr_bullets])
            # print_styled(f"Lines from wargear and special rules + the following sections: {headers}", STYLES.GREEN)
            # print(wargear_and_on)
            # print_styled("Special Rules", STYLES.GREEN)
            # print(self.special_rules_text)

        # At this point wargear and on no longer has any special rules or profiles.
        # progressively split wargear and on in reverse order, till we get back up to just the wargear and special rules
        header_sections = {}
        for header in reversed(headers):
            was_split, wargear_and_on, content = split_at_header(header, wargear_and_on)
            if was_split:
                header_sections[header] = content

        # print_styled("Upper Half without any special rules text", STYLES.GREEN)
        # print("\n".join(upper_half.splitlines() + wargear_and_on.splitlines()))

        # If special rules, split wargear_and_on at that position
        # instead of using the find column and split there code.
        wargear = wargear_and_on  # Default, assume no special rules and this is just wargear.
        special_rules_list = ""
        if "Special Rules" in wargear_and_on:
            sr_row_index = text_utils.get_index_of_line_with_headers(wargear_and_on, "Special Rules")
            sr_col_index = wargear_and_on.splitlines()[sr_row_index].index("Special Rules")

            # At this point, wargear and on is just wargear and special rules,
            # So we can split it with our two-column split code.
            _, wargear, special_rules_list, _ = \
                text_utils.split_into_columns_at_divider(wargear_and_on, sr_col_index, debug_print_level=0)

        # Now lets put everything together:
        new_text = "".join(
            [profiles, upper_half, wargear, special_rules_list] + [header_sections[header] for header in
                                                                   reversed(header_sections.keys())]
        )
        return new_text

    def split_before_line_before_statline(self, raw_text):
        """
        Split at the SECOND occurrence of a statline in a given block
        :param raw_text:
        :return:
        """
        occurrence = 0
        prev_line_with_text = 0
        lines = raw_text.split("\n")
        for index, line in enumerate(lines):
            if self.does_line_contain_profile_header(line):
                occurrence += 1
                if occurrence < 2:
                    continue
                return "\n".join(lines[:prev_line_with_text]), "\n".join(lines[prev_line_with_text:])
            if line.strip() != "":
                prev_line_with_text = index
        return raw_text, ""

    def process_unit(self, unit_text):
        print_styled("Cleaned Unit Text:", STYLES.DARKCYAN)
        print_styled(unit_text, STYLES.CYAN)
        # First get the name, from what should hopefully be the first line in raw_unit
        unit_name = ""
        points = None
        for line in unit_text.split("\n"):
            if line.strip() != "":
                unit_name += line.strip()
                if not self.game.NAME_HAS_DOTS or "..." in unit_name:
                    break
                else:
                    unit_name += " "  # Add a space between lines.

        if "..." in unit_name:
            points = unit_name[unit_name.rindex('.') + 1:].strip()
            unit_name = unit_name[:unit_name.index('.')].strip()

        if points and ("p" in points.lower()):
            points = points[:points.lower().rindex("p")].strip()
            if points.isdigit():
                points = int(points)
            else:
                points = None
                print_styled("Was not able to read points", STYLES.RED)

        max_selections_of_unit = None
        if unit_name.startswith("0-"):
            first_space = unit_name.index(" ")
            max_selections_of_unit = unit_name[:first_space][2]  # 3rd character should max
            unit_name = unit_name[first_space + 1:]

        constructed_unit = RawUnit(name=unit_name, points=points, page=self)
        if max_selections_of_unit:
            constructed_unit.max = int(max_selections_of_unit)

        if self.game.FORCE_ORG_IN_FLAVOR:
            for line in self.flavor_text_col.splitlines():
                if line.strip().isupper():
                    constructed_unit.force_org = line.strip()

                    break
        names = []
        stats = []
        # Then, get the table out of the header.
        unit_profile_headers = self.get_unit_profile_headers(unit_text)

        num_data_cells = len(unit_profile_headers)
        in_table = False
        in_note = False
        profile_index = -1
        lines = unit_text.split("\n")
        profiles_end = None
        for line_number, line in enumerate(lines):
            # print(f"{line}, In Table: {in_table}, In Note: {in_note}")
            if self.does_line_contain_profile_header(line):
                in_table = True
                in_note = False  # Note has ended
                continue
            if in_table and line.startswith("Note:"):
                stats[profile_index] += [line.split("Note: ")[1]]
                in_note = True
                continue

            if line.startswith(self.game.ProfileLocator):
                profiles_end = line_number
                break
            if in_note:
                stats[profile_index][-1] += " " + line
                continue
            if in_table:
                cells = line.split()
                if len(cells) < num_data_cells:
                    # partial row that's a continuation of a previous row
                    names[profile_index] += cells
                    continue
                names.append(cells[:-num_data_cells])
                stats.append(cells[-num_data_cells:])
                profile_index += 1

        # rejoin stats and name components.
        for index, name in enumerate(names):
            name = ' '.join(name)
            raw_profile = RawModel(name=name, page=self, stats=dict(zip(unit_profile_headers + ['Note'],
                                                                        stats[index])))
            constructed_unit.model_profiles.append(raw_profile)

        unit_text = "\n".join(lines[profiles_end:])

        # From the bottom up, split out the individual sections
        for header in reversed(self.game.UNIT_SUBHEADINGS):
            was_split, unit_text, content = split_at_header(header, unit_text, header_at_end_of_line=False)
            if was_split:
                if content[len(header):].splitlines()[0].strip() == ":":
                    constructed_unit.subheadings[header] = "\n".join(
                        content.splitlines()[1:])  # Cut the header label off.

                else:
                    constructed_unit.subheadings[header] = content[len(header):]  # Cut the header label off.

        self.units.append(constructed_unit)

    def process_weapon_profiles(self):
        if not self.special_rules_text:
            return

        print_styled("Unprocessed non-unit text:", STYLES.GREEN)
        print_styled(self.special_rules_text, STYLES.YELLOW)

        non_weapon_lines = []

        weapons_dicts = []

        # The following is similar to the unit profile detection, but is likely worse at handling notes.
        # The best we can do to detect the end of note/notes is the end of a sentence, or the start of a new table.
        # If a line ends a sentence of a note, it'll unfortunately chop off the

        num_data_cells = len(self.game.WEAPON_PROFILE_TABLE_HEADERS) - 1
        # Minus one as we deal with special rules separately

        if not len(self.game.WEAPON_PROFILE_TABLE_HEADERS):
            raise Exception("No weapon profile headers defined")

        last_header = self.game.WEAPON_PROFILE_TABLE_HEADERS[-1]

        in_table = False
        in_note = False
        name_prefix = ""
        profile_index = -1
        sr_col_index = 0
        name_col_index = 0

        for line in self.special_rules_text.split("\n"):
            # print(f"{line}, In Table: {in_table}, In Note: {in_note}")
            if text_utils.does_line_contain_header(line, ["R", "S", "Special Rules", "AP"]):
                print("Malformed table line!")
                self.weapons.append(RawProfile(name=f"Unable to read profile from {self.special_rules_text}",
                                               page=self, stats={}))
                self.special_rules_text = "\n".join(line)
                return
            if text_utils.does_line_contain_header(line, self.game.WEAPON_PROFILE_TABLE_HEADERS):
                if not line.lstrip().startswith(self.game.WEAPON_PROFILE_TABLE_HEADERS[0]):
                    name_prefix = line.split(f" {self.game.WEAPON_PROFILE_TABLE_HEADERS[0]} ")[0].strip()
                sr_col_index = line.index(last_header)

                in_table = True
                in_note = False  # A previous note has ended
                continue
            if in_table and line.startswith("Notes:"):
                weapons_dicts[profile_index]["Notes"] = line.split("Notes: ")[1]
                in_note = True
                continue
            if in_table and line.startswith("Note:"):
                weapons_dicts[profile_index]["Notes"] = line.split("Note: ")[1]
                in_note = True
                continue
            if in_note:
                weapons_dicts[profile_index]["Notes"] += " " + line
                if line.rstrip().endswith("."):
                    # The best we can do to detect the end of note/notes is the end of a sentence.
                    in_note = False
                    in_table = False
                    name_col_index = 0
                continue
            if line.strip() == "":
                in_table = False
                in_note = False
                name_col_index = 0
            if name_col_index and line[:name_col_index].strip() != "":
                # If this line is before the first letter of the name column, the table has probably ended.
                in_table = False
                in_note = False
                name_col_index = 0
            if in_table:
                name_and_stats = line
                special_rules = ""
                if len(line) > sr_col_index:
                    name_and_stats = line[:sr_col_index]
                    if name_and_stats.strip() == "":
                        # print(f"Profile index: {profile_index} Weapons dicts: {str(weapons_dicts)}")
                        weapons_dicts[profile_index][last_header] += line[sr_col_index:]
                        continue  # Not a full line, just a continuation of special rules.
                    special_rules = line[sr_col_index:]

                # print("Name and stats: ", name_and_stats)
                # print("Special Rules:  ", special_rules)

                # Name and stats
                cells = name_and_stats.split()
                if len(cells) < num_data_cells:
                    if profile_index < 0:  # partial row that's a continuation of the name
                        name_prefix += " " + name_and_stats.strip()
                    else:  # partial row that's a continuation of a previous row's name
                        weapons_dicts[profile_index]["Name"] += cells
                    continue

                name = cells[:-num_data_cells]
                stats_for_line = cells[-num_data_cells:]
                if special_rules and special_rules[0].islower():
                    # If our headers are misaligned, we're in the middle of a word,
                    # scoot over all the cells and re-append the start of the word to the type.
                    name = cells[:-num_data_cells - 1]  # Shift over one
                    stats_for_line = cells[-num_data_cells - 1:-1]  # Shift over one
                    # This was cropped off the start of special rules, so re-append it
                    special_rules = cells[-1] + special_rules
                if ")" in cells[-num_data_cells] and self.game.COMBINED_ARTILLERY_PROFILE:
                    # Special handling for artillery
                    # print(cells)
                    name = cells[:-(num_data_cells + 2)]

                    stats_for_line = [cells[-5],
                                      " ".join(cells[-4:-2]),
                                      " ".join(cells[-2:]), ]
                if name and not name_col_index:
                    name_col_index = line.index(name[0])
                if (name_prefix
                        # Don't append the name prefix if it's already in the name
                        and name_prefix not in " ".join(name)
                        and name_prefix != "Weapon"):
                    name = [name_prefix, "-"] + name
                stats_for_line.append(special_rules)
                weapons_dicts.append(dict(zip(self.game.WEAPON_PROFILE_TABLE_HEADERS,
                                              stats_for_line)))
                profile_index += 1
                weapons_dicts[profile_index]["Name"] = name
            else:
                in_table = False
                in_note = False
                name_prefix = ""
                if line.strip().isdigit():
                    # Probably a page number, skip this line.
                    continue
                non_weapon_lines.append(line)

        # rejoin stats and name components.
        for weapon_as_dict in weapons_dicts:
            name = ' '.join(weapon_as_dict.pop("Name"))  # Remove the name from the dict
            raw_profile = RawProfile(name=name, page=self, stats=weapon_as_dict)
            self.weapons.append(raw_profile)

        self.special_rules_text = "\n".join(non_weapon_lines)

    def process_special_rules(self):
        if not self.special_rules_text:
            return
        # print_styled("Special rules raw text to process:", STYLES.DARKCYAN)
        # print(self.special_rules_text)
        # TODO: Handle extraneous lines starting in '*Note' that should be part of the unit.
        # TODO: If there's a weapon profile in one of or before the special rules, pull it out.
        first_paragraph_is_flavor = self.game.IN_DATASHEET_FIRST_PARAGRAPH_IS_FLAVOR if len(self.units) \
            else self.game.FIRST_PARAGRAPH_IS_FLAVOR

        no_flavor_if_colon = self.page_type == PageTypes.WARGEAR

        page_content_as_dict = text_to_rules_dict(self.special_rules_text, first_paragraph_is_flavor,
                                                  no_flavor_if_colon)

        # Heresy wargear pages are identical to special rules pages, except they are wargear.
        if self.page_type == PageTypes.WARGEAR:
            self.wargear_dict = page_content_as_dict
            return
        if self.page_type == PageTypes.TYPES_AND_SUBTYPES:
            self.types_and_subtypes_dict = page_content_as_dict
            return

        # Model-specific wargear can end up in the special rules dict.
        # TODO pull wargear out on a model specific page by checking the unit's wargear
        self.special_rules_dict = page_content_as_dict
