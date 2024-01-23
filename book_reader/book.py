from book_reader.pdf_page import PdfPage


class Book:
    def __init__(self, file_path, settings: {str: bool} = None, system=None):
        if settings is None:
            settings = {}
        self.settings = settings
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
        with open(self.file_path, "rb") as f:
            pdf = pdftotext.PDF(f, physical=True)

            page_offset = 0  # TODO: Pull page offset from some sort of settings file
            for page_counter, page_text in enumerate(pdf):
                if page_counter < 5 and not page_offset:
                    self.try_get_page_offset(page_text, page_counter)
                if page_offset:
                    page_number = page_counter + page_offset
                    # print(f"Page number is {page_number}, from {page_counter} + {page_offset}")
                else:
                    page_number = page_counter
                page = PdfPage(self, page_text, page_number)
                self.pages.append(page)

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
