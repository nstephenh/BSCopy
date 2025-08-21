import traceback

from book_reader.constants import PageTypes
from book_reader.page import Page
from book_reader.raw_entry import RawUnit, RawProfile, RawModel
from system.game.game import Game
from import_scripts.text_to_rules import text_to_rules_dict
from system.game.heresy3e import Heresy3e
from util import text_utils
from util.log_util import STYLES, print_styled
from util.text_utils import split_into_columns, split_at_header, split_after_header, get_line_indent, split_at_unindent, \
    un_justify, split_on_header_line, split_2_columns_at_right_header, get_2nd_colum_index_from_header, \
    split_into_columns_at_divider


class PdfPage(Page):

    def __init__(self, book, raw_text, page_number, file_page_number, prev_page_type=None):
        super().__init__(book, page_number, file_page_number)
        self.raw_text = text_utils.replace_quote_alikes(raw_text)
        self.raw_text = text_utils.remove_copyright_footer(self.raw_text)
        self.cleaned_text = None
        self.faq_entries = []
        if self.page_number and self.raw_text.rstrip().endswith(str(self.page_number)):
            self.raw_text = self.raw_text.rstrip()[:-len(str(self.page_number))]

        debug_specific_page = 0
        if debug_specific_page:
            if self.page_number < debug_specific_page:
                return  # For debugging
            if self.page_number > debug_specific_page:
                exit()  # For debugging

            print_styled(f"\nPage {self.page_number} is Type: {self.page_type}", STYLES.GREEN)
            # print (self.raw_text)

        if self.raw_text.strip() == "" or len(self.raw_text.strip().splitlines()) < 3:
            self.page_type = PageTypes.BLANK_OR_IGNORED
            return

        if not self.page_type or self.page_type == PageTypes.UNIT_PROFILES:
            self.try_handle_units()
        if not self.page_type or self.page_type == PageTypes.SPECIAL_RULES:
            self.handle_special_rules_page(prev_page_type)
        if not self.page_type or self.page_type == PageTypes.WEAPON_PROFILES:
            self.handle_weapon_profiles_page(prev_page_type)
        if not self.page_type or self.page_type == PageTypes.WARGEAR:
            self.handle_wargear_page(prev_page_type)
        if not self.page_type or self.page_type == PageTypes.TYPES_AND_SUBTYPES:
            self.handle_types_page(prev_page_type)
        if self.page_type == PageTypes.FAQ:
            self.handle_faq_page()  # For now just read into cleaned_text

        # Pull out any special rules or profiles, either the main body of the page, or set from units.
        self.process_weapon_profiles()
        if self.page_type != PageTypes.WEAPON_PROFILES:  # A weapon page shouldn't have any special rules on it.
            self.process_special_rules()

        for unit in self.units:
            unit.page_weapons = self.weapons
            try:  # TODO Do want to delay this?
                unit.process_subheadings()
            except Exception as e:
                print(e)
                print_styled(traceback.format_exc(), style=STYLES.RED)

    def try_handle_units(self):
        if self.book.system.game.ProfileLocator in self.raw_text:
            self.get_text_units()
            if self.units_text is None or self.units_text == "":
                print(self.page_number, "has no unit text, here is it's raw text:")
                print(self.raw_text)
                self.page_type = PageTypes.BLANK_OR_IGNORED
                return
            for unit in self.units_text:
                if unit is None:
                    print(f"Blank unit on page {self.page_number}:")
                    print(self.raw_text)
                    continue
                try:
                    self.process_unit(unit)
                except Exception as e:
                    print(f"Could not process unit on page {self.page_number}")
                    print(e)
                    print_styled(traceback.format_exc(), style=STYLES.RED)

            if len(self.units):  # if we found any units, this page is a units page
                self.page_type = PageTypes.UNIT_PROFILES

    def handle_special_rules_page(self, prev_page_type):
        # Special rules pages are two-column format
        has_special_rules_header = "Special Rules".lower() in self.raw_text.lower().lstrip().splitlines()[2]
        header_text, col_1, col_2 = self.handle_simple_two_column_page()

        # If page doesn't have a special rules header and isn't after a previous special rules page,
        # then it's not a special rules page.
        if not has_special_rules_header and not prev_page_type == PageTypes.SPECIAL_RULES:
            return

        self.page_type = PageTypes.SPECIAL_RULES

        self.special_rules_text = col_1 + "\n" + col_2

    def handle_weapon_profiles_page(self, prev_page_type):
        if not self.page_type:
            has_armoury_header = "Armoury".lower() in self.raw_text.lstrip().splitlines()[0].lower()
            if not has_armoury_header and not prev_page_type == PageTypes.WEAPON_PROFILES:
                return
        self.page_type = PageTypes.WEAPON_PROFILES
        self.special_rules_text = self.raw_text

    def handle_wargear_page(self, prev_page_type):
        header_text, col_1, col_2 = self.handle_simple_two_column_page()
        first_line = ""
        if header_text.lstrip().splitlines():
            first_line = header_text.lstrip().splitlines()[0].lower()
        has_wargear_header = "Wargear".lower() in first_line and "ADDITIONAL".lower() not in first_line
        if not has_wargear_header and not prev_page_type == PageTypes.WARGEAR:
            return
        self.page_type = PageTypes.WARGEAR
        self.special_rules_text = col_1 + "\n" + col_2

    def handle_simple_two_column_page(self):
        header_text, col_1, col_2, _ = split_into_columns(self.raw_text, ensure_middle=True, debug_print_level=0)
        self.cleaned_text = "\n".join([header_text, col_1, col_2])
        return header_text, col_1, col_2

    def handle_faq_page(self):
        self.handle_simple_two_column_page()
        faq_entries = []
        entry = None

        for line in self.cleaned_text.splitlines():
            if "(Page" in line:
                if entry:
                    faq_entries.append(entry)
                    # Put the existing entry on the list and then make a new one
                entry = {
                    "Title": line.split("(Page")[0],
                    "Page": line.split("(Page")[-1].rstrip().rstrip(")"),
                    "Text": "",
                }
            elif entry:  # Assuming we've started an entry, append it
                entry['Text'] += "\n" + line
        # Push the last entry on the list (if it exists)
        if entry:
            faq_entries.append(entry)

        self.faq_entries = faq_entries

    def handle_types_page(self, prev_page_type):
        has_types_header = "Unit Types".lower() in self.raw_text.lstrip().splitlines()[0].lower()
        if not has_types_header and not prev_page_type == PageTypes.TYPES_AND_SUBTYPES:
            return
        self.page_type = PageTypes.TYPES_AND_SUBTYPES
        self.special_rules_text = self.raw_text

    @property
    def game(self) -> 'Game':
        return self.book.system.game

    def get_number_of_units(self) -> int:
        return self.raw_text.count(self.book.system.game.ProfileLocator)

    def does_line_contain_profile_header(self, line) -> bool:
        for header_type, header_raw_and_full in self.game.UNIT_PROFILE_TABLE_HEADER_OPTIONS.items():
            header_raw = header_raw_and_full.get('raw')
            if text_utils.does_line_contain_header(line, header_raw):
                return header_type
        return False

    def get_unit_profile_headers(self, text: str) -> (str, [str]):
        if not len(self.game.UNIT_PROFILE_TABLE_HEADER_OPTIONS):
            raise Exception("No UNIT PROFILE HEADERS")
        for line in text.splitlines():
            for header_type, header_raw_and_full in self.game.UNIT_PROFILE_TABLE_HEADER_OPTIONS.items():
                header_raw = header_raw_and_full.get('raw')
                if text_utils.does_line_contain_header(line, header_raw):
                    return header_type, header_raw
        return None, None

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

        if self.game.GAME_FORMAT_CONSTANT == Heresy3e.GAME_FORMAT_CONSTANT:
            # New implementation for HH3
            self.units_text = [self.cleanup_unit_text_hh3(num_units)]
            return
        elif self.game.COULD_HAVE_STAGGERED_HEADERS:  # HH2
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
            try:
                ut_index = uc_and_ut.index("Unit Type")
            except ValueError:
                # This page looks like a unit page somehow but isn't (crusade cards on page 69 of panoptica)
                return

            _, uc, ut, _ = text_utils.split_into_columns_at_divider(uc_and_ut, ut_index,
                                                                    debug_print_level=0)

            rules_text = "".join([profiles, uc, ut, bottom_half])

            if rules_text:
                cleaned_unit_text = self.cleanup_unit_text(rules_text)
                if cleaned_unit_text:
                    self.units_text = [cleaned_unit_text]
                    self.cleaned_text = self.flavor_text_col + "\n" + cleaned_unit_text
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

    def cleanup_unit_text_hh3(self, rules_text) -> str:

        profile_locator = self.game.ProfileLocator

        # profile_locator should be the second line, and above that should be the unit name.
        was_split, unit_name, everything_but_name = split_on_header_line(self.raw_text, profile_locator)
        if not was_split:
            print(f"Could not split at {profile_locator}")
            exit()
            # If this datasheet doesn't have Unit composition,
            # this is being called in the wrong context

        # Split at the stat lines.

        was_split, header_and_flavor, profiles_and_on = self.split_before_statline(everything_but_name)
        if not was_split:
            print(f"Could not find any statlines")
            return ""  # If this datasheet doesn't have a statline, something is wrong.

        # Remove flavor text
        was_split, unit_composition, flavor = split_at_unindent(header_and_flavor)
        # Start putting content into our unit.
        name_and_comp = un_justify(unit_name + "\n" + unit_composition)

        # The first header should be the first on our list.
        was_split, profiles, wargear_list_and_on = split_on_header_line(profiles_and_on, self.game.UNIT_SUBHEADINGS[0])

        # Anything after the subheadings will be indented (2 spaces, at least so far)
        # Find where the unit subheadings end and the traits/special rules/wargear begin
        for indented_heading in ["  THE ", "  WARGEAR", " SPECIAL RULES"]:  # THE %SOMETHING% TRAIT or TYPE
            was_split, unit_subheadings_text, non_unit_rules = split_on_header_line(wargear_list_and_on,
                                                                                    indented_heading,
                                                                                    True)
            if was_split:
                break

        self.special_rules_text = non_unit_rules

        # Now split at any of our after 2-column headers ("Options" and "Access points")
        two_colum_section, after_2_col_section = self.split_subheadings_after_2_col_section(unit_subheadings_text)

        # Wargear and special rules profiles will be indented
        was_split, left_col, right_col = split_2_columns_at_right_header(two_colum_section, "SPECIAL RULES")
        if not was_split:
            print(f"Not a valid HH3 datasheet, there should be a * None Special Rules column")
            return ""
        unit_rules_text = "\n".join([name_and_comp, profiles, left_col, right_col, after_2_col_section])

        return unit_rules_text

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
        headers = self.game.SUBHEADINGS_AFTER_2_COL_SECTION
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
        wargear_and_on, after_2_col_section = self.split_subheadings_after_2_col_section(wargear_and_on)

        # print_styled("Upper Half without any special rules text", STYLES.GREEN)
        # print("\n".join(upper_half.splitlines() + wargear_and_on.splitlines()))

        wargear, special_rules_list, = split_2_columns_at_right_header(wargear_and_on, "Special Rules")

        # Now lets put everything together:
        new_text = "\n".join(  # Add a newline between sections to ensure no overlap if table doesn't end in one.
            [profiles, upper_half, wargear, special_rules_list, after_2_col_section]
        )
        return new_text

    def split_subheadings_after_2_col_section(self, subheadings_text) -> (str, str):
        """
        Remove the subheadings after the 2-column section
        :param subheadings_text: The parts of the datasheet only containing subheadings
        :return: the 2-column section, the part after the 2-column section.
        """
        # progressively split up in reverse order, till we get back up to just the 2-column section.
        headers = self.game.SUBHEADINGS_AFTER_2_COL_SECTION
        header_sections = {}
        for header in reversed(headers):
            was_split, subheadings_text, subheading_content = split_at_header(header, subheadings_text)
            if was_split:
                header_sections[header] = subheading_content
        if self.game.SUBHEADINGS_AFTER_2_COL_ARE_2_COL:  # HH3 only right now, make "SPECIAL RULES" a parameter for generic
            index = get_2nd_colum_index_from_header("SPECIAL RULES", subheadings_text)
            if index is None:
                print_styled("Could not find 'SPECIAL RULES' in: ", STYLES.RED)
                print(subheadings_text)
                exit()
            for header in header_sections:
                _, left, right, _ = split_into_columns_at_divider(header_sections[header], index, debug_print_level=0)
                header_sections[header] = header + "\n" + left + "\n" + right  # Header gets caught in non-col lines
        after_2_col_section = "\n".join([header_sections[header] for header in reversed(header_sections.keys())])
        return subheadings_text, after_2_col_section

    def split_before_statline(self, raw_text, expected_occurrences=1) -> (bool, str, str):
        """
        Split at the occurrence of a statline in a given block. Will trim out blank lines.
        :param raw_text:
        :param expected_occurrences:   set to 2, I can only assume, for tables which have the headers repeated,
                                        and you need the second occurrence.

        :return:
        """
        occurrence = 0
        prev_line_with_text = 0
        lines = raw_text.split("\n")
        for index, line in enumerate(lines):
            if self.does_line_contain_profile_header(line):
                occurrence += 1
                if occurrence < expected_occurrences:
                    continue
                return True, "\n".join(lines[:prev_line_with_text + 1]), "\n".join(lines[prev_line_with_text + 1:])
            if line.strip() != "":
                prev_line_with_text = index
        return False, raw_text, ""

    def process_unit(self, unit_text):
        # print_styled("Cleaned Unit Text:", STYLES.DARKCYAN)
        # print_styled(unit_text, STYLES.CYAN)
        if self.game.GAME_FORMAT_CONSTANT == Heresy3e.GAME_FORMAT_CONSTANT:
            self.process_hh3_unit(unit_text)
        else:
            self.process_hh2_unit(unit_text)

    def process_hh3_unit(self, unit_text):
        # profile_locator should be the second line, and above that should be the unit name.
        _, unit_name, everything_but_name = split_on_header_line(unit_text, self.game.ProfileLocator)
        unit_name = unit_name.splitlines()[0].strip()  # Multiline names are subtitles, ignore the subtitle.
        # For now assume no line wrapping
        unit_comp_line = everything_but_name.splitlines()[0]
        split_comp_line = unit_comp_line.strip().split(" ")
        if split_comp_line[-1].lower() != "points":
            print(f"Expected points in {unit_comp_line}")
            return
        points = split_comp_line[-2]

        unit = RawUnit(name=unit_name, points=points, page=self)
        self.process_unit_common(unit, unit_text)

    def process_hh2_unit(self, unit_text):
        # First get the name, from what should hopefully be the first line in raw_unit
        unit_name = ""
        points = None
        for line in unit_text.split("\n"):
            if self.does_line_contain_profile_header(line):
                break  # Stop if we hit a profile header
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

        raw_unit = RawUnit(name=unit_name, points=points, page=self)

        if self.game.FORCE_ORG_IN_FLAVOR:
            for line in self.flavor_text_col.splitlines():
                if line.strip().isupper():
                    raw_unit.force_org = line.strip()

                    break

        self.process_unit_common(raw_unit, unit_text)

    def process_unit_common(self, raw_unit: RawUnit, unit_text):
        unit_name = raw_unit.name
        if unit_name.startswith("0-"):
            first_space = unit_name.index(" ")
            max_selections_of_unit = unit_name[:first_space][2]  # 3rd character should max
            unit_name = unit_name[first_space + 1:]
            if max_selections_of_unit:
                raw_unit.max = int(max_selections_of_unit)
                raw_unit.name = unit_name

        names = []
        stats = []
        # Then, get the table out of the header.
        unit_profile_type, unit_profile_headers = self.get_unit_profile_headers(unit_text)
        if unit_profile_type is None:
            print(f"Unable to read unit profile from page {self.page_number}")
            return

        num_data_cells = len(unit_profile_headers)
        in_table = False
        in_note = False
        profile_index = -1
        lines = unit_text.split("\n")
        profiles_end = None
        for line_number, line in enumerate(lines):
            print(f"{line}, In Table: {in_table}, In Note: {in_note}")
            if self.does_line_contain_profile_header(line):
                in_table = True
                in_note = False  # Note has ended
                continue
            if in_table and line.startswith("Note:"):
                stats[profile_index] += [line.split("Note: ")[1]]
                in_note = True
                continue
            # hh2 profile locator is after stats
            if in_table and line.startswith(self.game.ProfileLocator):
                profiles_end = line_number
                break
            # hh3 profile locator is before, but WARGEAR should always be right after
            if line.startswith(self.game.UNIT_SUBHEADINGS[0]):
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
                                                                        stats[index])), profile_type=unit_profile_type)
            raw_unit.model_profiles.append(raw_profile)

        unit_text = "\n".join(lines[profiles_end:])

        # From the bottom up, split out the individual sections
        for header in reversed(self.game.UNIT_SUBHEADINGS):
            was_split, unit_text, content = split_at_header(header, unit_text, header_at_end_of_line=False)
            if header.endswith(":"):
                header = header[:-1]  # Strip colon of the end of header for our cleaned data
            if was_split:
                if content[len(header):].splitlines()[0].strip() == ":":
                    raw_unit.subheadings[header] = "\n".join(
                        content.splitlines()[1:])  # If we leave a colon behind on the name, strip it off

                else:
                    raw_unit.subheadings[header] = content[len(header):]  # Cut the header label off.

        self.units.append(raw_unit)

    def process_weapon_profiles(self):
        if not self.special_rules_text:
            return

        # print_styled("Unprocessed non-unit text:", STYLES.GREEN)
        # print_styled(self.special_rules_text, STYLES.YELLOW)

        # The following is similar to the unit profile detection, but is likely worse at handling notes.
        # The best we can do to detect the end of note/notes is the end of a sentence, or the start of a new table.
        # If a line ends a sentence of a note, it'll unfortunately chop off the

        if not len(self.game.WEAPON_PROFILE_TABLE_HEADER_OPTIONS):
            raise Exception("No weapon profile headers defined")

        for profile_name, header_raw_and_full_dict in self.game.WEAPON_PROFILE_TABLE_HEADER_OPTIONS.items():
            self.process_weapons_of_1_profile_type(profile_name, header_raw_and_full_dict['raw'])

    def process_weapons_of_1_profile_type(self, profile_name, headers):

        non_weapon_lines = []

        weapons_dicts = []

        num_data_cells = len(headers) - self.game.NUM_WEAPON_HEADERS_THAT_ARE_TEXT
        # Deal with Special rules and traits separately

        sr_header = headers[-self.game.NUM_WEAPON_HEADERS_THAT_ARE_TEXT]
        traits_header = headers[-1]

        in_table = False
        in_note = False
        name_prefix = ""
        name_counter = 0
        profile_index = -1
        sr_col_index = 0
        name_col_index = 0
        traits_col_index = 0

        for line in self.special_rules_text.split("\n"):
            # print(f"{line}, In Table: {in_table}, In Note: {in_note}")
            if text_utils.does_line_contain_header(line, ["R", "S", "Special Rules", "AP"]):
                print("Malformed table line!")  # The old world specific check
                self.weapons.append(RawProfile(name=f"Unable to read profile from {self.special_rules_text}",
                                               page=self, stats={}))
                self.special_rules_text = "\n".join(line)
                return
            if text_utils.does_line_contain_header(line, headers):
                if not (line.lstrip().startswith(headers[0])
                        or line.lstrip().startswith(profile_name)):
                    name_prefix = line.split(f" {headers[0]} ")[0].strip()
                else:
                    name_prefix = ""  # Clear the name prefix as we are starting a new table.
                sr_col_index = line.index(sr_header)
                if self.game.NUM_WEAPON_HEADERS_THAT_ARE_TEXT == 2:
                    traits_col_index = line.index(traits_header)

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
            if not in_note and text_utils.looks_like_sentence(line):
                in_table = False
                name_col_index = 0
            if name_col_index and line[:name_col_index].strip() != "":
                # If this line is before the first letter of the name column, the table has probably ended.
                in_table = False
                in_note = False
                name_col_index = 0
            if in_table:
                name_and_stats = line
                special_rules = ""
                traits = ""
                if len(line) > sr_col_index:
                    name_and_stats = line[:sr_col_index]
                    if name_and_stats.strip() == "":  # Not a full line, just a continuation of special rules.
                        # print(f"Profile index: {profile_index} Weapons dicts: {str(weapons_dicts)}")
                        if traits_col_index > 0:
                            weapons_dicts[profile_index][sr_header] += " " + line[
                                                                             sr_col_index:traits_col_index].rstrip()
                            weapons_dicts[profile_index][traits_header] += " " + line[traits_col_index:].rstrip()
                            continue
                        weapons_dicts[profile_index][sr_header] += " " + line[sr_col_index:].rstrip()
                        continue
                    special_rules = line[sr_col_index:]
                    if traits_col_index > 0:
                        special_rules = line[sr_col_index:traits_col_index].rstrip()
                        traits = line[traits_col_index:].rstrip()

                # print("Name and stats: ", name_and_stats)
                # print("Special Rules:  ", special_rules)
                # if traits:
                #     print("Traits:  ", traits)

                # Name and stats
                cells = name_and_stats.split()
                if len(cells) < num_data_cells or special_rules.strip() == "":
                    name_col_text = name_and_stats.strip()
                    if profile_index < 0:  # partial row that's a continuation a table header name (old world)
                        name_prefix += " " + name_col_text
                    elif special_rules.strip() == "" and self.game.DASHED_WEAPON_MODES:
                        name_prefix = name_col_text  # Unlikely to be weapon name spillover,
                        # they are fairly short and the column is generally quite wide in heresy.
                        # There could be an edge case for this in weapon profiles I'm missing.
                    else:  # partial row that's a continuation of a previous row's name
                        weapons_dicts[profile_index]["Name"] += cells
                    continue

                name_cells = cells[:-num_data_cells]
                stats_for_line = cells[-num_data_cells:]

                if special_rules and special_rules[0].islower():
                    # If our headers are misaligned, we're in the middle of a word,
                    # scoot over all the cells and re-append the start of the word to the type.
                    name_cells = cells[:-num_data_cells - 1]  # Shift over one
                    stats_for_line = cells[-num_data_cells - 1:-1]  # Shift over one
                    # This was cropped off the start of special rules, so re-append it
                    special_rules = cells[-1] + special_rules
                if ")" in cells[-num_data_cells] and self.game.COMBINED_ARTILLERY_PROFILE:
                    # Special handling for artillery
                    # print(cells)
                    name_cells = cells[:-(num_data_cells + 2)]

                    stats_for_line = [cells[-5],
                                      " ".join(cells[-4:-2]),
                                      " ".join(cells[-2:]), ]
                if name_cells and name_cells[-1] == "-" and name_cells[-2].isdigit():
                    # if our name is ending in a range, stitch it back together
                    range_cells = name_cells[-2:]
                    name_cells = name_cells[:-2]
                    stats_for_line[0] = " ".join(range_cells) + stats_for_line[0]

                if name_cells and not name_col_index:
                    name_col_index = line.index(name_cells[0])

                if name_prefix:
                    if len(name_cells) == 0 or " ".join(name_cells) == "Up to":
                        # Special handling for multirange heresy weapons
                        stats_for_line[0] = " ".join(name_cells + [stats_for_line[0]])
                        name_counter += 1  # number these profiles as 1, 2, 3
                        name_cells = [f"{name_prefix} ({name_counter})"]
                    elif self.game.DASHED_WEAPON_MODES and name_cells[0] != "-":
                        # If we've exited the list of options, clear the name prefix
                        name_prefix = ""
                        name_counter = 0

                    if (name_prefix
                            # Don't append the name prefix if it's already in the name
                            and name_prefix not in " ".join(name_cells)):
                        if self.game.DASHED_WEAPON_MODES:
                            name_cells = [name_prefix] + name_cells
                        else:
                            name_cells = [name_prefix, "-"] + name_cells

                stats_for_line.append(special_rules)
                if traits:
                    stats_for_line.append(traits)
                for i, stat in enumerate(stats_for_line):
                    stats_for_line[i] = stat.strip()
                weapons_dicts.append(dict(zip(headers, stats_for_line)))

                profile_index += 1
                weapons_dicts[profile_index]["Name"] = name_cells
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
            raw_profile = RawProfile(name=name, page=self, stats=weapon_as_dict, profile_type=profile_name)
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
