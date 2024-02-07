from typing import TYPE_CHECKING

from util import text_utils
from util.log_util import STYLES, print_styled
from util.text_utils import split_at_dot, remove_plural, split_at_dash, option_process_line, make_plural

if TYPE_CHECKING:
    from book_reader.page import Page


class RawProfile:
    def __init__(self, name: str, page: 'Page', stats: dict[str: str], special_rules: list[str] = None):
        self.name: str = name
        self.page = page
        self.stats: dict[str: str] = stats
        self.special_rules: list[str] = []
        if special_rules:
            for rule in special_rules:
                self.special_rules.append(rule.strip())

    @property
    def game(self):
        return self.page.book.system.game

    def get_diffable_profile(self, profile_type: str = None):
        text = ""
        print_dict = {"Name": self.name}
        print_dict.update(self.stats)
        for key, item in print_dict.items():
            if profile_type:
                key = self.game.get_full_characteristic_name(key, profile_type)
            text += f"{key}: {item}\n"
        if self.special_rules:
            text += f"Special Rules: {self.get_special_rules_list()}"
        # Printing each rule was a good idea but not great in practice for diffing.
        # for rule in self.special_rules:
        #    text += f"Special Rule: {rule}\n"
        return text

    def get_special_rules_list(self):
        return ", ".join(self.special_rules)

    def serialize(self):
        return {'Name': self.name, 'Stats': self.stats}


class RawModel(RawProfile):

    def __init__(self, page, name: str, stats: dict[str: str], special_rules: list[str] = None):
        super().__init__(name, page, stats, special_rules)
        self.min = None
        self.max = None
        self.default_wargear: [str] = []
        self.original_wargear: [str] = []
        self.wargear_descriptions: {str: str} = {}
        self.wargear_profiles: [RawProfile] = []
        self.options_groups: [OptionGroup] = []
        self.unit_type_text: str = ""  # We use this as part of heresy characteristics
        self.type_and_subtypes: [str] = []
        self.pts = None

    def serialize(self):
        dict_to_return = super().serialize()
        dict_to_return.update(
            {
                "Type and Subtypes": self.type_and_subtypes,
                "Min": self.min,
                "Max": self.max,
                "Wargear": self.default_wargear
            })
        if len(self.wargear_descriptions) > 0:
            dict_to_return["Wargear Descriptions"] = self.wargear_descriptions

        if len(self.wargear_profiles) > 0:
            dict_to_return["Wargear Profiles"] = [profile.serialize() for profile in self.wargear_profiles]

        if len(self.options_groups) > 0:
            dict_to_return["Option Groups"] = [group.serialize() for group in self.options_groups]

        return dict_to_return


class Option:
    def __init__(self, name, pts=0):
        self.name = name
        self.pts = pts
        self.default = False  # Not yet implemented

    def serialize(self):
        return {"Name": self.name, "pts": self.pts}


class OptionGroup:
    def __init__(self, title):
        self.title = title
        self.max = 1
        self.min = 0
        self.options: [Option] = []

    def remove(self, name):
        # Get all options that don't have a name equal to the existing option.
        self.options = [option for option in self.options if option.name != name]

    def option_names(self):
        return [option for option in self.options]

    def serialize(self):
        return {
            "Title": self.title,
            "min": self.min,
            "max": self.max,
            "Options": [option.serialize() for option in self.options],

        }


class RawUnit:
    def __init__(self, name: str, page: 'Page' = None, points: int = None):
        self.name = name
        self.page = page
        self.points = points
        self.force_org: str | None = None
        self.model_profiles: list[RawModel] = []
        self.unit_type_text = None
        self.special_rules: list[str] = []
        self.special_rule_descriptions: {str: str} = {}
        self.subheadings: {str: str} = {}
        self.max = None
        self.errors = ""
        self.unit_options: [OptionGroup] = []
        self.page_special_rules = {}  # Can also include some wargear
        self.page_weapons = []

    def serialize(self) -> dict:
        dict_to_return = {'Name': self.name}
        if self.points is not None:
            dict_to_return['Points'] = self.points
        if self.force_org is not None:
            dict_to_return['Force Org'] = self.force_org
        if len(self.model_profiles) > 0:
            dict_to_return['Profiles'] = [profile.serialize() for profile in self.model_profiles]
        if len(self.unit_options) > 0:
            dict_to_return["Unit Options"] = [group.serialize() for group in self.unit_options]
        if len(self.special_rules) > 0:
            dict_to_return["Special Rules"] = self.special_rules
        if len(self.special_rule_descriptions) > 0:
            dict_to_return["Special Rule Descriptions"] = self.special_rule_descriptions
        if len(self.subheadings) > 0:
            dict_to_return["Subheadings"] = self.subheadings
        if len(self.errors):
            dict_to_return["Errors"] = self.errors
        return dict_to_return

    def process_subheadings(self):
        # Set the default with unit composition.
        if "Unit Composition" in self.subheadings:
            for line in split_at_dot(self.subheadings.pop("Unit Composition").splitlines()):
                first_space = line.index(' ')
                default_number = int(line[:first_space])
                model_name = line[first_space:].strip()
                model_profile = self.get_profile_for_name(model_name)
                if model_profile is None:
                    return
                model_profile.min = default_number
                model_profile.max = default_number

        if "Wargear" in self.subheadings:
            for model in self.model_profiles:
                for line in split_at_dot(self.subheadings["Wargear"].splitlines()):
                    if "only)" in line and model.name not in line:
                        continue
                    if "(" in line:
                        line = line.split("(")[0].strip()
                    model.original_wargear.append(line)
                    model.default_wargear.append(line)

                # Check the special rules list for wargear in case it's not in the shared list.
                for special_rule_name, text in self.page_special_rules.items():
                    print(special_rule_name)
                    if special_rule_name in model.original_wargear:
                        model.wargear_descriptions[special_rule_name] = text
                for weapon in filter(lambda x: x.name in model.original_wargear, self.page_weapons):
                    model.wargear_profiles.append(weapon)
            self.subheadings.pop("Wargear")

        # Going through all the options also gets us the points per model we wil use later.
        if "Options:" in self.subheadings:
            option_groups_text = text_utils.un_justify(self.subheadings.pop("Options:"), move_bullets=True)
            extra_special_options = ["Aspect Shrines", "Legiones Consularis", "Pater Consularis"]
            for extra_special_option in extra_special_options:
                if extra_special_option in option_groups_text:
                    index = option_groups_text.index(extra_special_option)
                    option_groups_text = option_groups_text[:index]
                    self.errors += "This unit has an extra special option not yet handled.\n"
                    break
            # print_styled(option_groups_text, STYLES.PURPLE)
            for line in split_at_dot(option_groups_text.splitlines()):
                self.process_option_group(line)

        if "Special Rules" in self.subheadings:
            self.special_rules = split_at_dot(self.subheadings.pop("Special Rules").splitlines())

            for special_rule_name, text in self.page_special_rules.items():
                if special_rule_name in self.special_rules:
                    self.special_rule_descriptions[special_rule_name] = text

        if "Unit Type" in self.subheadings:
            for line in split_at_dot(self.subheadings.pop("Unit Type").splitlines()):
                self.process_unit_types(line)

    def get_profile_for_name(self, model_name):
        if model_name.endswith("*"):
            model_name = model_name[:-1]
            self.errors += f"{model_name} has an asterisk! What does it mean?!? \n"
        model_name_options = [model_name, remove_plural(model_name), make_plural(model_name)]
        model_profile = None
        for option in model_name_options:
            for profile in self.model_profiles:
                if profile.name == option:
                    model_profile = profile
                    break
        if model_profile is None:
            for option in model_name_options:
                for profile in self.model_profiles:
                    if profile.name.endswith(option):
                        model_profile = profile
                        break
            if model_profile is None:
                error_message = \
                    f"Could not find profile for {model_name} in {[profile.name for profile in self.model_profiles]} \n"
                print_styled(error_message, STYLES.RED)
                self.errors += error_message
                # raise Exception(error_message)
        return model_profile

    def process_option_group(self, line):
        if ":" not in line:
            self.errors += f"{line} is not an option group\n" + "There could be invisible text on the page\n"
            return
        first_colon = line.index(":")
        option_title = line[:first_colon] + ":"
        options = split_at_dash(line[first_colon + 1:])
        print(option_title)

        # This is an "additional models" line
        if "may include" in option_title:
            for option in options:
                name, pts = option_process_line(option)  # set points, don't do anything with entries
                if name.startswith("Up to"):
                    additional_models_str = name.split('Up to')[1].split('additional')[0].strip()
                    if additional_models_str.isdigit():
                        additional_models = int(additional_models_str)
                    else:
                        additional_models = text_utils.number_word_to_int(additional_models_str)
                    model_name = name.split('additional ')[1]
                    print(f"{model_name} x{additional_models} at {pts} each")
                    profile = self.get_profile_for_name(model_name)
                    if profile is None:
                        continue  # get_profile_for_name will have added the error.
                    profile.pts = pts
                    profile.max += additional_models
            return  # this section was points per model options, so we don't need to generate an options group.

        option_group = OptionGroup(title=option_title)

        option_group.max = 1
        if "and/or" in option_title or "up to two" in option_title:
            option_group.max = 2

        option_models = []  # Temporary list of models that this option group applies to.

        for model in self.model_profiles:
            model_name = model.name
            if "Any model" in option_title or \
                    (not option_title.startswith("One") and model_name in option_title):
                # If the option is a "One model may" we leave this on the
                option_models.append(model)
        if len(option_models) > 0:
            print(f"\tApplies to {', '.join([model.name for model in option_models])}")

        from_wargear_list = False  # If the first entry is from the wargear list, and thus the default

        if "exchange" in option_title:
            # For wargear that gets exchanged, remove it from the default wargear, and add it to this list.
            add_to_options_list = []
            for model in option_models:
                wargear_removed_by_this_option = []
                for wargear in model.original_wargear:
                    # Default wargear shouldn't have 'and' in it, so we can pull straight from the list.
                    if wargear in option_title:
                        wargear_removed_by_this_option.append(wargear)
                for wargear in wargear_removed_by_this_option:
                    if wargear not in model.default_wargear:
                        self.errors += (
                            f"{wargear} is in two option lists for {model.name}, you will need to combine "
                            f"them by hand.\n")
                        continue  # We can't remove it from the list because we already have
                    model.default_wargear.remove(wargear)
                    if wargear not in add_to_options_list:  # To ensure we don't add it to our shared list twice.
                        add_to_options_list.append(wargear)
            for option in add_to_options_list:  # Add the option to the start of the options list
                options = [option + " ... "] + options
                # It'll be listed as free in the options list for that dropdown
                from_wargear_list = True  # use this to set the default
        elif "up to" in option_title:
            option_group.min = 0
        defaulted_message = ", default (from wargear list)" if from_wargear_list else ""

        # Read name and points from the source text
        for option in options:
            print("Option:", option)
            if option.strip() == "":
                continue
            name, pts = option_process_line(option)
            if line.endswith(" each"):
                self.errors += f"The option '{name}' may need a 'multiply by number of models' modifier\n"
            print(f"\t\t{name} for {pts} pts{defaulted_message}")
            defaulted_message = ""  # Clear our defaulted message now that we've shown it.
            option_group.options.append(Option(name=name, pts=pts))

        for model in option_models:
            model.options_groups.append(option_group)
        if len(option_models) == 0 and len(option_group.options):
            self.unit_options.append(option_group)

    def process_unit_types(self, line):
        model_name = None
        if ":" in line:
            model_name = line.split(":")[0].strip()
            unit_type_text = line.split(":")[1].strip()
        else:
            # Unit type should apply to all models
            unit_type_text = line.strip()

        if "(" in unit_type_text:
            type_and_subtypes = [unit_type_text.split("(")[0].strip()]
            type_and_subtypes += [text.strip() for text in unit_type_text.split("(")[1][:-1].strip().split(",")]
        else:
            type_and_subtypes = [unit_type_text]

        # Apply the type and subtypes to the profile
        for model in self.model_profiles:
            if model_name and model_name != model.name:
                continue
            model.unit_type_text = unit_type_text
            model.type_and_subtypes = type_and_subtypes
