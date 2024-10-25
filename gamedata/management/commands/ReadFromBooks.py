import os

from django.core.management import BaseCommand
from tqdm import tqdm

import settings
from book_reader.book import Book
from book_reader.constants import ReadSettingsKeys
from system.system import System

from gamedata.models import Publication, RawPage, Publisher, Game, GameEdition, PublishedDocument


class Command(BaseCommand):
    help = "Creates the Horus Heresy System"

    def handle(self, *args, **options):
        import_heresy_books()


def import_heresy_books():
    books_to_read = []
    for file_name in os.listdir("imports/"):
        filepath = os.path.join("imports/", file_name)
        if os.path.isdir(filepath) or os.path.splitext(file_name)[1] not in ['.epub', '.pdf']:
            continue  # Skip this iteration
        books_to_read.append(file_name)

    raw_import_settings = {
        ReadSettingsKeys.FIRST_PARAGRAPH_IS_FLAVOR: True,
        ReadSettingsKeys.ACTIONS: [
        ],
    }

    i = 1
    raw_files = {}

    # We need a system to load the default settings.
    system = System('noop', settings=settings.default_settings)
    for file_name in books_to_read:
        file_no_ext = os.path.splitext(file_name)[0]
        filepath = os.path.join("imports/", file_name)
        print('\r', end="")
        print(f"Reading book ({i}/{len(books_to_read)}): {filepath}", end="")
        # Publication and target file will be defined in book_json_config
        raw_files[file_no_ext] = Book(filepath, system, settings=raw_import_settings)
        i += 1

    gw, _ = Publisher.objects.get_or_create(name="Games Workshop", abbreviation="GW")
    pano, _ = Publisher.objects.get_or_create(name="Liber Panoptica Team", abbreviation="Pano")
    hh, _ = Game.objects.get_or_create(name="Warhammer: The Horus Heresy", abbreviation="HH")
    hh2, _ = GameEdition.objects.get_or_create(game=hh, release_year=2022)

    for file, book, in raw_files.items():
        print(file)
        name_components = file.split(' - ')
        if len(name_components) in [3, 4]:
            publisher_abbreviation = name_components[0]
            edition_abbreviation = name_components[1]  # assume all books are from this publisher
            name = name_components[2]
            version = "published"
            if len(name_components) == 4:
                version = name_components[3]
        else:
            raise Exception(f"Book {file} is not in the expected name format of " +
                            "'publisher - game edition - title - version (optional)'")

        page_offset = 0
        if "(" in name:  # for "Reduced" which has no title page
            page_offset = 0
            name = name.split("(")[0]
        elif publisher_abbreviation == "GW":  # GW Title page offset
            page_offset = -1

        if edition_abbreviation != "HH2":
            raise Exception(f"Currently we only support the edition HH2")
        try:
            publisher = Publisher.objects.get(abbreviation=publisher_abbreviation)
        except Publisher.DoesNotExist:
            raise Exception(f"Publisher with abbreviation {publisher_abbreviation} does not exist")

        pub, _ = Publication.objects.get_or_create(name=name, publisher=publisher, edition=hh2)
        doc, _ = PublishedDocument.objects.get_or_create(publication=pub, version=version)
        for page in tqdm(book.pages, unit="Pages"):
            dbPage, _ = RawPage.objects.get_or_create(document=doc,
                                                      file_page_number=page.file_page_number)
            if page.file_page_number - page_offset > 0:
                dbPage.actual_page_number = page.file_page_number - page_offset
            dbPage.raw_text = page.raw_text
            dbPage.save()
