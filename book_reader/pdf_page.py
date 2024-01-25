import os

from book_reader.constants import PageTypes
from book_reader.page import Page
from book_reader.raw_entry import RawUnit, RawProfile
from text_to_rules import text_to_rules_dict
from util.log_util import style_text, STYLES, print_styled
from util.text_utils import split_into_columns, split_at_header, split_after_header


class PdfPage(Page):

    def __init__(self, book, raw_text, page_number, prev_page_type=None):
        super().__init__(book, page_number)
        self.special_rules_text = None
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
        if header_index >= len(self.game.UNIT_PROFILE_TABLE_HEADERS):
            return True
        header_to_find = self.game.UNIT_PROFILE_TABLE_HEADERS[header_index]
        if header_to_find in line:
            # print(f"Found {header_to_find} in {line}")
            line = line[line.index(header_to_find):]
            return self.does_line_contain_profile_header(line, header_index + 1)
        return False

    def get_text_units(self):
        num_units = self.get_number_of_units()
        if num_units == 0:
            return
        page_header, col_1_text, col_2_text, _ = split_into_columns(self.raw_text)[0]

        # If a datasheet, it should have two columns in the center of the page.
        if self.book.system.game.ProfileLocator not in col_1_text and self.book.system.game.ProfileLocator not in col_2_text:
            return False  # Not a datasheet
        rules_text = col_1_text if self.book.system.game.ProfileLocator in col_1_text else col_2_text
        flavor_text = col_2_text if self.book.system.game.ProfileLocator in col_2_text else col_1_text

        rules_text = page_header + rules_text

        if num_units == 2:  # To handle, don't split if there are two stat lines with "Note" in between.
            unit_1, unit_2 = self.split_before_line_before_statline(rules_text)
            self.units_text = [self.get_text_unit(unit_1), self.get_text_unit(unit_2)]
            return

        if num_units > 3:
            print_styled("There are 3 units on this page:",STYLES.RED)
            print(self.raw_text)
            raise NotImplemented("Have not yet handled 3 units on a page")

        self.units_text = [self.get_text_unit(rules_text)]

    def get_text_unit(self, rules_text):
        profile_locator = self.game.ProfileLocator

        # First, try and split this datasheet into parts based on known headers
        if not self.game.MIDDLE_IN_2_COLUMN:
            if self.game.ENDS_AFTER_SPECIAL_RULES:
                rules_text, self.special_rules_text = split_after_header(rules_text, "Special Rules:")
            return rules_text

        upper_half = rules_text
        was_split, profiles, upper_half = split_at_header(profile_locator, upper_half, header_at_end_of_line=False)
        if not was_split:
            print(f"Could not split at {profile_locator}")
            return  # If this datasheet doesn't have "Unit composition, something is wrong

        # Access points comes before Options, though a sheet is not guaranteed to have either.
        was_split, upper_half, lower_half = split_at_header("Access Points", upper_half)
        if not was_split:
            _, upper_half, lower_half = split_at_header(self.book.system.game.OPTIONS, upper_half)

        upper_half, comp_and_wargear, type_and_special_rules, _ = split_into_columns(upper_half, debug_print_level=0)[0]

        # Now lets put everything together:
        print_styled("Reconstructed Datasheet", STYLES.GREEN)
        return "".join(
            [profiles, comp_and_wargear, type_and_special_rules, upper_half, lower_half]
        )

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
        print_styled("Raw Unit:", STYLES.DARKCYAN)
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
        profile_index = -1
        lines = unit_text.split("\n")
        profiles_end = None
        for line_number, line in enumerate(lines):
            print(line)
            if in_table and line.startswith("Note:"):
                print("Note line detected: " + line)
                stats[profile_index] += [line.split("Note:")[1]]
                continue
            if line.strip() == "" or line.startswith(self.game.ProfileLocator):
                profiles_end = line_number
                break
            if self.does_line_contain_profile_header(line):
                in_table = True
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
