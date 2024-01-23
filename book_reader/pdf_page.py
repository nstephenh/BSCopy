import os

from book_reader.page import Page
from util.log_util import style_text, STYLES, print_styled
from util.text_utils import split_into_columns, split_at_header


class PdfPage(Page):

    def __init__(self, book, raw_text, page_number):
        super().__init__(book)
        self.raw_text = raw_text
        self.page_number = page_number

        if "Unit Composition" in raw_text:
            self.unit = self.read_datasheet()

    def read_datasheet(self):

        page_header, col_1_text, col_2_text, _ = split_into_columns(self.raw_text)[0]

        # If a datasheet, it should have two columns in the center of the page.
        if "Unit Composition" not in col_1_text and "Unit Composition" not in col_2_text:
            return False  # Not a datasheet
        datasheet_text = col_1_text if "Unit Composition" in col_1_text else col_2_text
        flavor_text = col_2_text if "Unit Composition" in col_2_text else col_1_text
        print_styled("Datasheet:", STYLES.RED)
        upper_half = datasheet_text
        # First, try and split this datasheet into parts based on known headers
        was_split, profiles, upper_half = split_at_header("Unit Composition", upper_half, header_at_end_of_line=False)
        if not was_split:
            print("Could not split at Unit Composition")
            return  # If this datasheet doesn't have "Unit composition, something is wrong

        # Access points comes before Options, though a sheet is not guaranteed to have either.
        was_split, upper_half, lower_half = split_at_header("Access Points", upper_half)
        if not was_split:
            _, upper_half, lower_half = split_at_header("Options", upper_half)

        upper_half, comp_and_wargear, type_and_special_rules, _ = split_into_columns(upper_half, debug_print_level=0)[0]

        # Now lets put everything together:
        print_styled("Reconstructed Datasheet", STYLES.GREEN)
        print("".join(
            [page_header, profiles, comp_and_wargear, type_and_special_rules, upper_half, lower_half]))
        # Could also print flavor text on the end if we wanted.
