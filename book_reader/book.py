import ebooklib
from ebooklib import epub

from book_reader.page import Page


class Book:
    def __init__(self, epub_path):

        book = epub.read_epub(epub_path)
        special_rules_text: dict[str: str] = {}
        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                Page(self, item)
