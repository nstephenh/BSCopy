import os

from book_reader.pdf_page import PdfPage

import subprocess as sp


class Book:
    def __init__(self, file_path, system, settings: {str: bool | str} = None, book_config: dict = None):
        if settings is None:
            settings = {}
        self.settings = settings
        if book_config is None:
            book_config = {}
        self.book_config = book_config

        self.file_path = file_path
        self.system = system
        self.pages = []
        if file_path.endswith('.epub'):
            self.read_as_epub()
        if file_path.endswith('.pdf'):
            self.read_as_pdf()

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
        try:
            import pdftotext
        except Exception as e:
            print("You probably need poppler installed via Conda")
            exit()
        self.pdftotext()  # Save a text file of the pdf.
        self.file_path = self.file_path.replace('.pdf', '.txt')
        with open(self.file_path, "r", encoding='utf-8') as f:
            pdf = f.read()
            # If the next page doesn't have information to help identify it,
            # we can guess that it's still the previous page type.
            prev_page_type = None
            page_offset = 0  # Consider pulling default page offset from book json.
            for page_counter, page_text in enumerate(pdf.split('')):
                if page_counter < 5 and not page_offset:  # Try getting page number for the first 5 pages.
                    self.try_get_page_offset(page_text, page_counter)
                if page_offset:
                    page_number = page_counter + page_offset
                    # print(f"Page number is {page_number}, from {page_counter} + {page_offset}")
                else:
                    page_number = page_counter
                page = PdfPage(self, page_text, page_number, prev_page_type=prev_page_type)
                self.pages.append(page)
                prev_page_type = page.page_type

    def pdftotext(self):
        """
        Generate a text rendering of a PDF file in the form of a list of lines.
        # Because the python wrapper doesn't give us as good of output...
        """
        # Need pdftotext 23, not 4.x
        path_to_pdftotext = os.path.expanduser("~/miniconda3/Library/bin/pdftotext.exe")
        args = [path_to_pdftotext, '-layout', '-enc', 'UTF-8', self.file_path]
        sp.run(
            args, stdout=sp.PIPE, stderr=sp.DEVNULL,
            check=True
        )

    @staticmethod
    def try_get_page_offset(page_text, page_counter):
        if page_text.count("\n") > 5:  # Assuming there are 5 lines to check,
            for line in page_text.split("\n")[-5:]:  # Check the last 5 lines
                line = line.strip()
                if line.isdigit():
                    page_read_from_pdf = int(line)
                    print(f"Page in pdf is {page_read_from_pdf}")
                    print(f"Page counter is {page_counter}")
                    return page_read_from_pdf - page_counter
        return None

    @staticmethod
    def range_dict_to_range(range_dict):
        start = range_dict["start"]
        end = range_dict["end"]
        return range(start, end + 1)
