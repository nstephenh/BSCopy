from django.core.management.base import BaseCommand

from gamedata.models import Game, GameEdition, GameMod


class Command(BaseCommand):
    help = "Build mods to the horus heresy system"

    def handle(self, *args, **options):
        print("Finding the existing systems")

        hh, _ = Game.objects.get_or_create(name="Warhammer: The Horus Heresy")
        first_ed, _ = GameEdition.objects.get_or_create(game=hh, release_year=2012)

        second_ed, _ = GameEdition.objects.get_or_create(game=hh, release_year=2022)
        GameMod.objects.get_or_create(edition=second_ed,
                                      name="Liber Panoptica - FAQ")
        GameMod.objects.get_or_create(edition=second_ed,
                                      name="Liber Panoptica - Errata")
        GameMod.objects.get_or_create(edition=second_ed,
                                      name="Liber Panoptica - Balance Change")
        GameMod.objects.get_or_create(edition=second_ed,
                                      name="Liber Panoptica - Additions")
        GameMod.objects.get_or_create(edition=second_ed,
                                      name="Addenda-Appalacia")
        GameMod.objects.get_or_create(edition=second_ed,
                                      name="Mournival")
