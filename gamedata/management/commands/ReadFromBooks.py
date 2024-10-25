import os

from django.core.management import BaseCommand
from tqdm import tqdm

from book_reader.constants import ReadSettingsKeys, Actions
from system.constants import SystemSettingsKeys, GameImportSpecs
from system.system import System

from gamedata.models import Publication, RawPage, Publisher, Game, GameEdition, PublishedDocument


class Command(BaseCommand):
    help = "Creates the Horus Heresy System"

    def handle(self, *args, **options):
        import_heresy_books()


def import_heresy_books():
    settings = {
        SystemSettingsKeys.GAME_IMPORT_SPEC: GameImportSpecs.HERESY,
    }
    raw_import_settings = {
        ReadSettingsKeys.FIRST_PARAGRAPH_IS_FLAVOR: True,
        ReadSettingsKeys.ACTIONS: [
            Actions.DUMP_TO_JSON,
        ],
    }
    base_heresy = System('horus-heresy',
                         settings=settings,
                         include_raw=True,
                         raw_import_settings=raw_import_settings)
    modded_heresy = System('horus-heresy-panoptica',
                           settings=settings,
                           include_raw=True,
                           raw_import_settings=raw_import_settings)
    dump_books_for_system(base_heresy)
    dump_books_for_system(modded_heresy)


def dump_books_for_system(system):
    gw, _ = Publisher.objects.get_or_create(name="Games Workshop", abbreviation="GW")
    pano, _ = Publisher.objects.get_or_create(name="Liber Panoptica Team", abbreviation="Pano")
    hh, _ = Game.objects.get_or_create(name="Warhammer: The Horus Heresy", abbreviation="HH")
    hh2, _ = GameEdition.objects.get_or_create(game=hh, release_year=2022)

    for file, book, in system.raw_files.items():
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
            dbPage.cleaned_text = page.cleaned_text
            dbPage.save()
