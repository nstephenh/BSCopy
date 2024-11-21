import json

from django.core.management.base import BaseCommand

from gamedata.models import Game, GameEdition, Publication, GameProfileType, GameCharacteristicType, Profile, \
    ProfileCharacteristic


class Command(BaseCommand):
    help = "Creates the Horus Heresy System"

    def handle(self, *args, **options):
        print("This was for importing data only from BattleScribe xml. It has been deprecated until re-implemented.")
        exit()
        print("Creating the Horus Heresy System")

        hh, _ = Game.objects.get_or_create(name="Warhammer: The Horus Heresy")
        first_ed, _ = GameEdition.objects.get_or_create(game=hh, release_year=2012)
        import_system_from_json(first_ed, 'horus-heresy-1e')

        second_ed, _ = GameEdition.objects.get_or_create(game=hh, release_year=2022)
        import_system_from_json(second_ed, 'horus-heresy')


def import_system_from_json(game_ed, system_name):
    data = json.load(open(f"./imports/{system_name}_profiles.json", 'r'))
    for publication in data.get('Publications', []):
        if publication['Name'] == "Github":
            continue  # Skip github
        print(f"Creating {publication['Name']}")
        import_builder_object(game_ed, Publication, publication)

    for profile_type in data.get('Profile Types', []):
        create_profile_type(game_ed, profile_type)

    for profile in data.get('Profiles', []):
        print(f"Creating {profile['Name']} ({profile['Type']})")
        import_profile(game_ed, profile)

    import_rules(data, game_ed)


def import_rules(data, game_ed):
    rule_profile_type = {
        "Name": "Rule",
        "Builder ID": "tag:rule",
        "Characteristics": [{
            "Name": "Text",
            "Builder ID": "tag:description",
        }]
    }
    rule_type = create_profile_type(game_ed, rule_profile_type)
    characteristic_type = GameCharacteristicType.objects.get(name="Text",
                                                             profile_type=rule_type)
    for rule in data.get('Rules', []):
        print(f"Creating {rule['Name']}")
        profile, _ = Profile.objects.get_or_create(builder_id=rule["Builder ID"],
                                                   edition=game_ed,
                                                   defaults={
                                                       "name": rule.get("Name"),
                                                       "profile_type": rule_type,
                                                   },
                                                   )
        pc, _ = ProfileCharacteristic.objects.get_or_create(profile=profile,
                                                            characteristic_type=characteristic_type)
        pc.value_text = rule['Text']
        pc.save()  # Update values


def create_profile_type(game_ed, profile_type):
    print(f"Creating {profile_type['Name']}")
    profile_type_object = import_builder_object(game_ed, GameProfileType, profile_type)
    for characteristic in profile_type.get('Characteristics', []):
        print(f"Creating {profile_type['Name']} {characteristic['Name']}")
        GameCharacteristicType.objects.get_or_create(
            builder_id=characteristic["Builder ID"],
            profile_type=profile_type_object,
            edition=game_ed,
            defaults={
                "name": characteristic['Name'],
                "abbreviation": characteristic['Name'],
            }
        )
    return profile_type_object


def import_builder_object(game_ed, model, data, defaults=None):
    default_defaults = {
        "name": data.get("Name")  # Don't overwrite a name if set.
    }
    if defaults is not None:
        default_defaults.update(defaults)
    instance, _ = model.objects.get_or_create(builder_id=data["Builder ID"],
                                              edition=game_ed,
                                              defaults=default_defaults,
                                              )
    if data.get("Page") and not instance.page:
        instance.page = data["Page"]

    if data.get("Publication ID") and not instance.publication:
        instance.publication = Publication.objects.get(builder_id=data["Publication ID"])

    instance.save()
    return instance


def import_profile(game_ed, data):
    profile_type = GameProfileType.objects.get(name=data["Type"], edition=game_ed)
    profile, _ = Profile.objects.get_or_create(builder_id=data["Builder ID"],
                                               edition=game_ed,
                                               defaults={
                                                   "name": data.get("Name"),
                                                   "profile_type": profile_type,
                                               },
                                               )
    for characteristic_type_name, value in data.get('Characteristics', {}).items():
        print(f"\t Setting {characteristic_type_name} to {value}")
        characteristic_type = GameCharacteristicType.objects.get(name=characteristic_type_name,
                                                                 profile_type=profile_type)
        pc, _ = ProfileCharacteristic.objects.get_or_create(profile=profile,
                                                            characteristic_type=characteristic_type)
        pc.value_text = value
        pc.save()  # Update values
