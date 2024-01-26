import os

from book_reader.constants import PageTypes
from book_reader.page import Page
from book_reader.raw_entry import RawUnit, RawProfile
from text_to_rules import text_to_rules_dict
from util import text_utils
from util.log_util import style_text, STYLES, print_styled
from util.text_utils import split_into_columns, split_at_header, split_after_header


class PdfPage(Page):

    def __init__(self, book, raw_text, page_number, prev_page_type=None):
        super().__init__(book, page_number)
        self.raw_text = raw_text
        self.page_number = page_number
        if self.raw_text.strip() == "":
            self.page_type = PageTypes.BLANK_OR_IGNORED
            return
        if not self.page_type or self.page_type == PageTypes.UNIT_PROFILES:
            self.try_handle_units()
        if not self.page_type or self.page_type == PageTypes.SPECIAL_RULES:  # If not a unit page, could be a page of special rules.
            self.handle_special_rules_page(prev_page_type)
        self.process_special_rules()

    def try_handle_units(self):
        if self.book.system.game.ProfileLocator in self.raw_text:
            self.get_text_units()
            for unit in self.units_text:
                self.process_unit(unit)
            if len(self.units):  # if we found any units, this page is a units page
                self.page_type = PageTypes.UNIT_PROFILES

    def handle_special_rules_page(self, prev_page_type):
        if any([("Special Rules" in line) for line in self.raw_text.splitlines()[:5]]) \
                or prev_page_type is PageTypes.SPECIAL_RULES:
            # Special rules pages are two-column format, and the header of the page is irrelevant
            header_text, col_1, col_2, _ = split_into_columns(self.raw_text)[0]
            if prev_page_type is PageTypes.SPECIAL_RULES:
                if header_text.strip() != "":
                    return  # If the next page has a header, then it's not a special rules page

            self.page_type = PageTypes.SPECIAL_RULES

            self.special_rules_text = col_1 + "\n" + col_2

    @property
    def game(self):
        return self.book.system.game

    def get_number_of_units(self):
        units = 0
        for line in self.raw_text.splitlines():
            if self.does_line_contain_profile_header(line):
                # print(f"Line contains profile header: {line}")
                units += 1
        return units

    def does_line_contain_profile_header(self, line, header_index=0):
        if self.game.UNIT_PROFILE_TABLE_HEADERS is None:
            raise Exception("No UNIT PROFILE HEADERS")
        return text_utils.does_line_contain_header(line, self.game.UNIT_PROFILE_TABLE_HEADERS)

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
            print("Has Stagger!")
            # TODO make this more generic
            line_with_wargear_header = text_utils.get_index_of_line_with_headers(self.raw_text,
                                                                                 ["Wargear"])

            lines = self.raw_text.splitlines()

            left_sidebar_divider_index = lines[line_with_wargear_header].index("Wargear")
            if left_sidebar_divider_index:  # Left flavor text
                _, flavor_text, rules_text, _ = text_utils.split_into_columns_at_divider(self.raw_text,
                                                                                         left_sidebar_divider_index,
                                                                                         debug_print_level=0)[0]
            else:  # Right flavor text, column detection should work.
                page_header, rules_text, flavor_text, _ = split_into_columns(self.raw_text, debug_print_level=0)[0]
                rules_text = page_header + rules_text

            line_with_wargear_header = text_utils.get_index_of_line_with_headers(rules_text,
                                                                                 ["Wargear"])
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
                                                                    debug_print_level=0)[0]

            rules_text = "".join([profiles, uc, ut, bottom_half])

            if rules_text:
                self.units_text = [self.cleanup_unit_text(rules_text)]
            return
        else:
            page_header, col_1_text, col_2_text, _ = split_into_columns(self.raw_text, debug_print_level=0)[0]

            # If a datasheet, it should have two columns in the center of the page.
            if self.book.system.game.ProfileLocator not in col_1_text and self.book.system.game.ProfileLocator not in col_2_text:
                return False  # Not a datasheet
            rules_text = col_1_text if self.book.system.game.ProfileLocator in col_1_text else col_2_text
            flavor_text = col_2_text if self.book.system.game.ProfileLocator in col_2_text else col_1_text

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

        # Go through sections in reverse order now:
        headers = ["Dedicated Transport:",
                   "Access Points:",
                   "Options:"
                   ]
        end_of_bullets = text_utils.get_first_non_list_or_header_line(wargear_and_on, headers)
        lines = wargear_and_on.splitlines()
        if end_of_bullets:  # Otherwise, there will be no options, access points, dedicated transport, etc
            self.special_rules_text = "\n".join(lines[end_of_bullets:])
            wargear_and_on = "\n".join(lines[:end_of_bullets])
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
                text_utils.split_into_columns_at_divider(wargear_and_on, sr_col_index, debug_print_level=0)[0]

        # Now lets put everything together:
        new_text = "".join(
            [profiles, upper_half, wargear, special_rules_list] + [header_sections[header] for header in
                                                                   header_sections.keys()]
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
        for line in unit_text.split("\n"):
            if line.strip() != "":
                unit_name = line.strip()
                break

        constructed_unit = RawUnit(name=unit_name)

        names = []
        stats = []
        # Then, get the table out of the header.
        num_data_cells = len(self.game.UNIT_PROFILE_TABLE_HEADERS)
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
            if in_note:
                stats[profile_index][-1] += " " + line
            if line.startswith(self.game.ProfileLocator):
                profiles_end = line_number
                break

            if in_table:
                cells = line.split()
                if len(cells) < num_data_cells:
                    # partial row that's a continuation of a previous row
                    names[profile_index] += cells
                    continue
                names.append(cells[:-num_data_cells])
                stats.append(cells[-num_data_cells:])
                profile_index += 1

        for index, name in enumerate(names):
            name = ' '.join(name)
            raw_profile = RawProfile(name=name, stats=dict(zip(self.game.UNIT_PROFILE_TABLE_HEADERS + ['Note'],
                                                               stats[index])))
            constructed_unit.model_profiles.append(raw_profile)

        constructed_unit.unit_text = "\n".join(lines[profiles_end:])

        self.units.append(constructed_unit)

    def process_special_rules(self):
        if not self.special_rules_text:
            return
        # print_styled("Special rules raw text to process:", STYLES.DARKCYAN)
        # print(self.special_rules_text)
        # TODO: Handle extraneous lines starting in '*Note' that should be part of the unit.
        # TODO: If there's a weapon profile in one of or before the special rules, pull it out.
        self.special_rules_dict = text_to_rules_dict(self.special_rules_text, self.game.FIRST_PARAGRAPH_IS_FLAVOR)
        # print(self.special_rules_dict)
