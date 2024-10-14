import json
import os

import settings
from book_reader.book import Book
from book_reader.constants import ReadSettingsKeys, Actions
from system.system import System

if __name__ == '__main__':

    system_name = "horus-heresy"

    books_to_read = []
    for file_name in os.listdir("../imports/"):
        filepath = os.path.join("../imports/", file_name)
        if os.path.isdir(filepath) or os.path.splitext(file_name)[1] not in ['.epub', '.pdf']:
            continue  # Skip this iteration
        books_to_read.append(file_name)

    raw_import_settings = {
        ReadSettingsKeys.FIRST_PARAGRAPH_IS_FLAVOR: True,
        ReadSettingsKeys.ACTIONS: [
        ],
    }
    json_config = {

    }
    i = 1
    raw_files = {}

    # We need a system to load the default settings.
    system = System('noop', settings=settings.default_settings)
    for file_name in books_to_read:
        file_no_ext = os.path.splitext(file_name)[0]
        filepath = os.path.join("../imports/", file_name)
        print('\r', end="")
        print(f"Reading book ({i}/{len(books_to_read)}): {filepath}", end="")
        # Publication and target file will be defined in book_json_config
        book_json_config = {

        }
        raw_files[file_no_ext] = Book(filepath, system, settings=raw_import_settings)
        i += 1

    json_export = []
    for file, book, in raw_files.items():
        print(file)
        pages = []
        for page in book.pages:
            pages.append({
                "Number": page.page_number,
                "Raw Text": page.raw_text,
                "Type": page.page_type,
            })
        json_export.append({
            "Book": file,
            "Pages": pages
        })

    with open(f'../exports/{system_name}_books.json', 'w') as outfile:
        json.dump(json_export, outfile, indent=2)
