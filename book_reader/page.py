from bs4 import BeautifulSoup, Tag

from util.log_util import print_styled


class Page:
    def __init__(self, book, page_item, settings: {str: bool} = None):
        if settings is None:
            settings = {}
        self.book = book
        self.special_rules_text: dict[str: str] = {}

        page_name = page_item.get_name()
        try:
            page_name_components = page_name.split('.xhtml')[0].split("-")
            try:
                page_range_start = int(page_name_components[0])
            except ValueError:
                page_range_start = int(page_name_components[0].split('_')[0])

            page_number = int(page_range_start) + int(page_name_components[-1]) - 1
        except ValueError:
            print(f"Could not get page number for {page_name}")
            self = None
            return
        self.page_number = page_number
        content = page_item.get_content()
        soup = BeautifulSoup(content)
        res = soup.get_text()
        special_rules_elements_by_name: dict[str: Tag] = {}

        first_paragraph_is_flavor = ('first_paragraph_is_flavor' in settings.keys()
                                     and settings['first_paragraph_is_flavor'])

        # Find all special rules elements in the text
        for sr_element in soup.find_all('p', {'class': 'Headers_H4'}):
            special_rule_name = sr_element.get_text().strip()
            if "..." in special_rule_name or not special_rule_name:
                continue  # not actually a special rule
            special_rules_elements_by_name[special_rule_name] = sr_element
        # for each element, find the text between it and the next element
        for special_rule_name, sr_element in special_rules_elements_by_name.items():
            next_paragraph = sr_element.findNext('p')
            if first_paragraph_is_flavor:  # Skip the first paragraph
                next_paragraph = next_paragraph.findNext('p')
            composed_text = ""
            while next_paragraph is not None:
                paragraph_text = next_paragraph.get_text().strip()
                if paragraph_text in special_rules_elements_by_name.keys() or not (
                        next_paragraph['class'][0] in ['Body-Black_Body-Italic', 'Body-Black_Body-', ]):
                    # We've reached the end of this special rule and are on to the next one.
                    # Or a section with different formatting
                    break
                composed_text += paragraph_text + "\n"  # otherwise, add to the rules text
                next_paragraph = next_paragraph.findNext('p')

            composed_text = composed_text.strip()
            if composed_text == "":
                continue  # Not actually a special rule or not a special rule with content
            self.special_rules_text[special_rule_name] = composed_text
            print_styled(special_rule_name)
            print(self.special_rules_text[special_rule_name])
