import os
import subprocess as sp
from typing import TYPE_CHECKING

from tqdm import tqdm

from book_reader.constants import ReadSettingsKeys, Actions
from book_reader.pdf_page import PdfPage
from util.log_util import print_styled, STYLES

if TYPE_CHECKING:
    from system.system_file import SystemFile


class Book:
    def __init__(self, file_path, system, settings: {str: bool | str} = None, book_config: dict = None):
        if settings is None:
            settings = {}
        self.settings = settings

        self.file_path = file_path
        self.system = system

        self.name = os.path.split(file_path)[1]

        self.page_configs = {}
        self.pages = []

        self.pub_id = None
        self.priority = 0
        self.target_file_name: str | None = None
        self.target_system_file: 'SystemFile' or None = None
        self.read_config(book_config)

        if file_path.endswith('.epub'):
            self.read_as_epub()
        if file_path.endswith('.pdf'):
            self.read_as_pdf()

    def read_config(self, book_config: dict or None):
        if book_config is None:
            return
        self.pub_id = book_config.get('pub_id')
        self.priority = book_config.get('priority', 0)

        # Only set target system file if we are doing more than dumping to json.
        actions = self.settings.get(ReadSettingsKeys.ACTIONS, [])
        skip_target_sys_file = (len(actions) == 1 and actions[0] == Actions.DUMP_TO_JSON)
        if not skip_target_sys_file:
            self.target_system_file = self.get_target_sys_file(book_config.get('target_file_name'))

        page_ranges = book_config.get('page_ranges', [])
        for page_range in page_ranges:
            if not skip_target_sys_file:
                target_system_file = self.get_target_sys_file(page_range.pop('target_file_name', None))
                page_range['target_system_file'] = target_system_file if target_system_file else self.target_system_file
            for i in range(page_range.pop('start'), page_range.pop('end') + 1):
                self.page_configs[i] = page_range

    def read_as_epub(self):
        import ebooklib
        from ebooklib import epub

        from book_reader.page import EpubPage

        self.pages = []
        book = epub.read_epub(self.file_path)
        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                page = EpubPage(self, item)
                if hasattr(page, 'page_number'):
                    self.pages.append(page)

    def read_as_pdf(self):
        self.pdftotext()  # Save a text file of the pdf.
        self.file_path = self.file_path.replace('.pdf', '.txt')
        with open(self.file_path, "r", encoding='utf-8') as f:
            pdf = f.read()
            # If the next page doesn't have information to help identify it,
            # we can guess that it's still the previous page type.
            prev_page_type = None
            page_offset = None  # Consider pulling default page offset from book json.
            for page_counter, page_text in tqdm(enumerate(pdf.split('')), unit="Pages"):
                page_number = try_get_page_number(page_text)
                if page_counter < 5 and page_offset is not None:  # Try getting page number for the first 5 pages.
                    page_offset = try_get_page_offset(page_text, page_counter)
                if page_number:
                    pass  # Use the page number from try get
                elif page_offset:
                    page_number = page_counter + page_offset
                    # print(f"Page number is {page_number}, from {page_counter} + {page_offset}")
                else:
                    page_number = page_counter
                page = PdfPage(self, page_text, page_number, prev_page_type=prev_page_type,
                               file_page_number=page_counter)
                self.pages.append(page)
                prev_page_type = page.page_type

    def pdftotext(self):
        """
        Generate a text rendering of a PDF file in the form of a list of lines.
        # Because the python wrapper doesn't give us as good of output...
        """
        # Need pdftotext 23, not 4.x
        path_to_pdftotext = os.path.expanduser("~/miniconda3/Library/bin/pdftotext.exe")
        program_args = ['-layout', '-enc', 'UTF-8', self.file_path]
        try:
            raise Exception("test")
            args = [path_to_pdftotext]
            args += program_args
            sp.run(
                args, stdout=sp.PIPE, stderr=sp.DEVNULL,
                check=True
            )
        except Exception:
            args = ['pdftotext']
            args += program_args
            sp.run(
                args, stdout=sp.PIPE, stderr=sp.DEVNULL,
                check=True
            )

    def get_target_sys_file(self, target_file_name):
        if not target_file_name:
            return
        target_system_file = next(filter(lambda sf: sf.name == target_file_name, self.system.files),
                                  None)
        if target_system_file is None:
            print_styled(f"\nPlease create a catalogue named {target_file_name} as defined in books.json,"
                         f" or remove the reference to it. ", STYLES.RED)
            exit(1)
        return target_system_file


def try_get_page_offset(page_text, page_counter):
    page_read_from_pdf = try_get_page_number(page_text)
    if page_read_from_pdf:
        print(f"Page in pdf is {page_read_from_pdf}")
        print(f"Page counter is {page_counter}")
        return page_read_from_pdf - page_counter
    return None


def try_get_page_number(page_text):
    if page_text.count("\n") > 5:  # Assuming there are 5 lines to check,
        for line in page_text.split("\n")[-5:]:  # Check the last 5 lines
            line = line.strip()
            if line.isdigit():
                page_read_from_pdf = int(line)
                return page_read_from_pdf
    return None
