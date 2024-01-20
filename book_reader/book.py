import ebooklib
from ebooklib import epub

from book_reader.page import Page


class Book:
    def __init__(self, epub_path, settings: {str: bool} = None):
        if settings is None:
            settings = {}
        self.pages = []
        book = epub.read_epub(epub_path)
        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                page = Page(self, item, settings)
                if hasattr(page, 'page_number'):
                    self.pages.append(page)
