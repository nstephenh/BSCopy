import os

from book_reader.page import Page
from util.log_util import style_text, STYLES, print_styled
from util.text_utils import split_into_columns, split_at_header, split_after_header


class PdfPage(Page):

    def __init__(self, book, raw_text, page_number):
        super().__init__(book)
        self.special_rules_raw = None
        self.raw_text = raw_text
        self.page_number = page_number
        if self.book.system.game.ProfileLocator in raw_text:
            self.get_units()
            for unit in self.units:
                print_styled("Unit Profile:", STYLES.DARKCYAN)
                print(unit)

    @property
    def game(self):
        return self.book.system.game

    def get_number_of_units(self):
        units = 0
        for line in self.raw_text.splitlines():
            if self.does_line_contain_profile_header(line):
                units += 1
        return units

    def does_line_contain_profile_header(self, line, header_index=0):
        if header_index >= len(self.game.UNIT_PROFILE_TABLE_HEADERS):
            return True
        header_to_find = self.game.UNIT_PROFILE_TABLE_HEADERS[header_index]
        if header_to_find in line:
            line = line[line.index(header_to_find):]
            return self.does_line_contain_profile_header(line, header_index + 1)
        return False

    def get_units(self):
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

        if num_units >= 2:
            pass  # TODO: Split the two units somehow
            return

        self.units = [self.get_unit_profile(rules_text)]

    def get_unit_profile(self, rules_text):
        profile_locator = self.game.ProfileLocator

        # First, try and split this datasheet into parts based on known headers
        if not self.game.MIDDLE_IN_2_COLUMN:
            if self.game.ENDS_AFTER_SPECIAL_RULES:
                rules_text, self.special_rules_raw = split_after_header(rules_text, "Special Rules:")
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
