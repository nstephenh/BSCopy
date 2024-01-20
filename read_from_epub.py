import os

import ebooklib
from bs4 import BeautifulSoup, Tag
from ebooklib import epub

from util.log_util import print_styled

if __name__ == '__main__':
    epub_path = ""
    for file in os.listdir("."):
        if file.endswith('epub'):
            epub_path = file
            break
    print(epub_path)
    book = epub.read_epub(epub_path)
    book_as_json = {}
    special_rules_text: dict[str: str] = {}
    for item in book.get_items():
        if item.get_type() == ebooklib.ITEM_DOCUMENT:
            page_name = item.get_name()
            page_number = None
            try:
                page_name_components = page_name.split('.xhtml')[0].split("-")
                page_range_start = 0
                try:
                    page_range_start = int(page_name_components[0])
                except ValueError:
                    page_range_start = int(page_name_components[0].split('_')[0])

                page_number = int(page_range_start) + int(page_name_components[-1]) - 1
                print(page_number)
            except ValueError:
                print(f"Could not get page number for {page_name}")
                continue
            content = item.get_content()
            soup = BeautifulSoup(content)
            res = soup.get_text()
            special_rules_elements_by_name: dict[str: Tag] = {}
            # Find all special rules elements in the text
            for sr_element in soup.find_all('p', {'class': 'Headers_H4'}):
                special_rule_name = sr_element.get_text().strip()
                if "..." in special_rule_name or not special_rule_name:
                    continue  # not actually a special rule
                special_rules_elements_by_name[special_rule_name] = sr_element
            # for each element, find the text between it and the next element
            for special_rule_name, sr_element in special_rules_elements_by_name.items():
                next_paragraph = sr_element.findNext('p')
                special_rules_text[special_rule_name] = ""
                while next_paragraph is not None:
                    paragraph_text = next_paragraph.get_text().strip()
                    if paragraph_text in special_rules_elements_by_name.keys():
                        # We've reached the end of this special rule and are on to the next one.
                        break
                    special_rules_text[special_rule_name] += paragraph_text + "\n"  # otherwise, add to the rules text
                    next_paragraph = next_paragraph.findNext('p')

                print_styled(special_rule_name)
                print(special_rules_text[special_rule_name])
