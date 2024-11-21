import os

from django.core.management import BaseCommand
from tqdm import tqdm

from book_reader.constants import ReadSettingsKeys, Actions
from system.constants import SystemSettingsKeys, GameImportSpecs
from system.system import System

from gamedata.models import Publication, RawPage, Publisher, Game, GameEdition, PublishedDocument, RawErrata, Unit, \
    Profile, ProfileCharacteristic, CharacteristicType, ProfileType, RawText


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
            version = "Published"
            if len(name_components) == 4:
                version = name_components[3]
        else:
            raise Exception(f"Book {file} is not in the expected name format of " +
                            "'publisher - game edition - title - version (optional)'")

        page_offset = 0
        if "(" in name:  # for "Reduced" which has no title page
            page_offset = 0
            name = name.split("(")[0].strip()
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
            db_page, _ = RawPage.objects.get_or_create(document=doc,
                                                       file_page_number=page.file_page_number)
            if page.file_page_number - page_offset > 0:
                db_page.actual_page_number = page.file_page_number - page_offset
            db_page.raw_text = page.raw_text
            db_page.cleaned_text = page.cleaned_text
            db_page.rules_text = page.special_rules_text
            db_page.save()
            for unit in page.units:
                store_unit_in_database(unit, db_page)

            # TODO: Set target docs after we load everything.
            # target_docs_for_errata = get_target_docs_for_errata(hh2, page)
            for faq in page.faq_entries:
                errata, _ = RawErrata.objects.get_or_create(page=db_page,
                                                            title=faq["Title"],
                                                            )
                errata.target_page = faq["Page"].strip()
                errata.text = faq["Text"]
                # errata.target_docs.set(target_docs_for_errata)
                errata.save()


def get_target_docs_for_errata(db_system, page):
    target_docs_for_errata = PublishedDocument.objects.none()
    if page.faq_entries:
        for eratta_target_name in page.target_books_for_errata:
            name_components = eratta_target_name.split(' - ')
            if len(name_components) not in [1, 2]:
                raise Exception(f"Errata Book Reference {eratta_target_name} is not in the expected name format of " +
                                "'title - version (optional)'")
            target_pub_name = name_components[0]

            pubs_for_target = PublishedDocument.objects.filter(
                publication__name=target_pub_name,
                publication__edition=db_system)
            if len(name_components) == 2:
                version = name_components[1]
                pubs_for_target.filter(version=version)
            if not pubs_for_target.exists():
                raise Exception(f"Unable to find the specified target document to errata: {eratta_target_name}")
            target_docs_for_errata |= pubs_for_target
    return target_docs_for_errata


def store_unit_in_database(unit, db_page):
    db_unit, _ = Unit.objects.get_or_create(page=db_page, name=unit.name)
    edition = db_page.document.publication.edition
    for model in unit.model_profiles:
        profile_type, _ = ProfileType.objects.get_or_create(edition=edition,
                                                            name=model.profile_type)
        # Profile doesn't link to a page but does link to a document and page number....
        db_profile, _ = Profile.objects.get_or_create(page_number=db_page.actual_page_number,
                                                      edition=edition,
                                                      document=db_page.document,
                                                      unit=db_unit,
                                                      profile_type=profile_type,
                                                      name=model.name)
        for characteristic_type, value in model.stats.items():
            db_characteristic_type, _ = CharacteristicType.objects.get_or_create(abbreviation=characteristic_type,
                                                                                 profile_type=profile_type,
                                                                                 edition=edition)
            pc, _ = ProfileCharacteristic.objects.get_or_create(profile=db_profile,
                                                                characteristic_type=db_characteristic_type)
            pc.value_text = value
            pc.save()
    for title, text in unit.subheadings.items():
        db_subheading, _ = RawText.objects.get_or_create(page=db_page, unit=db_unit, title=title)
        db_subheading.text = text
        db_subheading.save()

