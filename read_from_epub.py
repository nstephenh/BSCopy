import os

import ebooklib
from bs4 import BeautifulSoup
from ebooklib import epub

if __name__ == '__main__':
    epub_path = ""
    for file in os.listdir("."):
        if file.endswith('epub'):
            epub_path = file
            break
    print(epub_path)
    book = epub.read_epub(epub_path)
    book_as_json = {}
    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            page_name = item.get_name()
            page_name_components = page_name.split('.xhtml')[0].split("-")
            page_number = int(page_name_components[0]) + int(page_name_components[-1]) - 1
            print(page_number)
            content = item.get_content()
            soup = BeautifulSoup(content)
            res = soup.get_text()
            for special_rule in soup.find_all('p', {'class': 'Headers_H4'}):
                special_rule_name = special_rule.get_text()
                if "..." in special_rule_name:
                    continue  # not actually a special rule
                print(special_rule_name)
