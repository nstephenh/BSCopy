from typing import TYPE_CHECKING

from system.game.heresy3e import Heresy3e
from util import text_utils
from util.log_util import STYLES, print_styled
from util.text_utils import split_at_dot, remove_plural, split_at_dash, option_process_line, make_plural, \
    split_at_header

if TYPE_CHECKING:
    from book_reader.page import Page


class RawEntry(object):
    def __init__(self, name: str, page: 'Page'):
        self.name: str = name
        self.page = page


class RawProfile(RawEntry):
    def __init__(self, name: str, page: 'Page', stats: dict[str: str], special_rules: list[str] = None,
                 profile_type=None):
        super().__init__(name, page)
        self.stats: dict[str: str] = stats
        self.profile_type: str = profile_type
        self.special_rules: list[str] = []
        if special_rules:
            for rule in special_rules:
                self.special_rules.append(rule.strip())
        # hh2 only, but not a problem for hh3 because of different naming
        elif self.profile_type == "Weapon" and stats.get('Type'):
            self.special_rules = [rule.strip() for rule in stats.get('Type').split(',')[1:]]

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


class HasOptionsMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)  # forwards all unused arguments
        self.option_groups: [OptionGroup] = []


class RawModel(HasOptionsMixin, RawProfile):

    def __init__(self, page, name: str, stats: dict[str: str], special_rules: list[str] = None,
                 profile_type: str = None):
        super().__init__(name, page, stats, special_rules, profile_type)
        self.min = None
        self.max = None
        self.default_wargear: [str] = []
        self.original_wargear: [str] = []
        self.wargear_descriptions: {str: str} = {}
        self.wargear_profiles: [RawProfile] = []
        self.unit_type_text: str = ""  # We use this as part of heresy characteristics
        self.type_and_subtypes: [str] = []
        self.pts = 0
        self.errors: [str] = []

    def serialize(self):
        dict_to_return = super().serialize()
        dict_to_return.update(
            {
                "Type and Subtypes": self.type_and_subtypes,
                "Min": self.min,
                "Max": self.max,
                "Wargear": self.default_wargear,
                "Pts": self.pts,
            })
        if len(self.wargear_descriptions) > 0:
            dict_to_return["Wargear Descriptions"] = self.wargear_descriptions

        if len(self.wargear_profiles) > 0:
            dict_to_return["Wargear Profiles"] = [profile.serialize() for profile in self.wargear_profiles]

        if len(self.option_groups) > 0:
            dict_to_return["Option Groups"] = [group.serialize() for group in self.option_groups]

        return dict_to_return


class Option:
    def __init__(self, name, pts=0, default=False):
        self.name = name
        self.pts = pts
        self.default = default  # Not yet implemented

    def serialize(self):
        as_dict = {"Name": self.name, "pts": self.pts}
        if self.default:
            as_dict["Default"] = self.default
        return as_dict


class OptionGroup:
    def __init__(self, title):
        self.title = title
        self.max = 1
        self.min = 0
        self.options: [Option] = []
        self.max_shared = False

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


class RawUnit(HasOptionsMixin, RawEntry):
    def __init__(self, name: str, page: 'Page', points: int = None):
        super().__init__(name, page)
        self.points = points
        self.force_org: str | None = None
        self.model_profiles: list[RawModel] = []
        self.unit_type_text = None
        self.warlord_traits: {str: str} = {}
        self.special_rules: list[str] = []
        self.special_rule_descriptions: {str: str} = {}
        self.subheadings: {str: str} = {}
        self.max = None
        self.errors: [str] = []
        self.page_weapons = []

    def serialize(self) -> dict:
        dict_to_return = {'Name': self.name}
        if self.points is not None:
            dict_to_return['Points'] = self.points
        if self.force_org is not None:
            dict_to_return['Force Org'] = self.force_org
        if len(self.model_profiles) > 0:
            dict_to_return['Profiles'] = [profile.serialize() for profile in self.model_profiles]
        if len(self.option_groups) > 0:
            dict_to_return["Unit Options"] = [group.serialize() for group in self.option_groups]
        if len(self.special_rules) > 0:
            dict_to_return["Special Rules"] = self.special_rules
        if len(self.special_rule_descriptions) > 0:
            dict_to_return["Special Rule Descriptions"] = self.special_rule_descriptions
        if len(self.subheadings) > 0:
            dict_to_return["Subheadings"] = self.subheadings
        if len(self.warlord_traits) > 0:
            dict_to_return["Warlord Traits"] = self.warlord_traits
        if len(self.errors):
            dict_to_return["Errors"] = self.errors
        return dict_to_return

    def process_subheadings(self):
        if self.page.book.system.game.GAME_FORMAT_CONSTANT == Heresy3e.GAME_FORMAT_CONSTANT:
            self.process_hh3_subheadings()
        else:
            self.process_hh2_subheadings()

    def process_hh3_subheadings(self):
        if "TYPE" in self.subheadings:
            for line in split_at_dot(self.subheadings.pop("TYPE").splitlines()):
                self.process_unit_types(line)
        else:
            print("What's wrong with the dark emissary?")
            print(self.serialize())
            return

        if "SPECIAL RULES" in self.subheadings:
            self.process_hh3_special_rules()
        else:
            print("What's wrong with the Chieftain Squad?")
            print(self.serialize())
            return

        self.process_hh3_unit_composition()

        self.process_wargear("WARGEAR")

        if "OPTIONS" in self.subheadings:
            option_groups_text = self.subheadings.pop("OPTIONS")
            # print_styled(f"Option Groups on {self.name}", STYLES.CYAN)
            # print_styled(option_groups_text, STYLES.PURPLE)
            for line in split_at_dot(option_groups_text.splitlines()):
                # First check to see if this is an option group like HH2 with a colon and dots.
                if self.process_option_group(line, do_not_apply_error=True):
                    continue
                # If not, then it's a line referencing either "this model" or "This model name"
                # print(line)
                option_title = None
                options_text_list = []
                if "exchanged for" in line:  # Some number of options
                    option_title = line.split("exchanged for ")[0] + "exchanged for "
                    options_as_text = line.split("exchanged for ")[1]
                    for text_opt in options_as_text.split(", "):
                        if " or " in text_opt:
                            options_text_list += text_opt.split(" or ")
                        else:
                            options_text_list.append(text_opt)

                elif "may have" in line:  # Only 1 option
                    option_title = line
                    options_as_text = line.split("may have")[1]
                    if "selected for it" in line:
                        selected_for_it_split = options_as_text.split("selected for it")
                        # Melta bombs [selected for it] for +5 Points.
                        options_text_list = [selected_for_it_split[0].rstrip() + selected_for_it_split[1].rstrip()]
                    else:
                        self.errors.append(f"Expected 'selected for it' in '{line}'")
                if option_title:
                    from_wargear_list, option_group, option_models, default_options = self.setup_option_group(
                        option_title, [])
                    if from_wargear_list:
                        option_group.min = option_group.max
                    if "exchange" in option_title and len(default_options) == 0:
                        self.errors.append(f"Exchange was not applied on {option_title}")
                    options_text_list = default_options + options_text_list

                    # print(f"Option Group: {option_title}")
                    # print(f"\tModels: {[model.name for model in option_models]}")
                    # print(f"\tSelections: {options_text_list}")
                    for option in options_text_list:
                        # print(f"\t\t{option}")
                        name = option
                        pts = 0
                        default = False
                        if option.endswith(" ... "):
                            name = option[:-5]
                            pts = 0
                            default = True
                        elif "for +" in option:
                            name, pts_str = option.split("for +")
                            if "each" in pts_str:
                                self.errors.append(
                                    f"The option '{name}' may need a 'multiply by number of models' modifier")
                            pts = int(pts_str.split(" Points")[0])
                        if name.startswith("one "):
                            name = name[4:]
                        option_group.options.append(Option(name=name.strip(), pts=pts, default=default))
                    # print(option_group.serialize())
                    for model in option_models:
                        model.option_groups.append(option_group)
                    if len(option_models) == 0 and len(option_group.options):
                        self.option_groups.append(option_group)
                else:
                    self.errors.append(f"Could not process option '{line}'.")

        # print(self.errors)

    def process_hh3_unit_composition(self):
        unit_comp_text = self.subheadings.pop("UNIT COMPOSITION")
        unit_comp_sections = []

        if "•" in unit_comp_text:
            unit_comp_sections = split_at_dot(unit_comp_text.splitlines())
            base_comp_line = unit_comp_sections.pop(0)
        else:
            base_comp_line = unit_comp_text

        for line in base_comp_line.split(","):
            self.set_default_composition_from_text_line(line)

        for option in unit_comp_sections:
            # print(option)
            if " +" in option:
                pts = int(option.split(" +")[1].split(" ")[0])
                option = option.split(" +")[0]
                if option.endswith(" at"):
                    option = option[:-3]
                if option.endswith(" for"):
                    option = option[:-4]
            elif " for Free" in option:
                pts = 0
                option = option.split(" for Free")[0]
            else:
                self.errors.append(f"Could not understand cost of {option}")
                continue
            if option.startswith("May include "):
                additional_models_str = option.split(' up to ')[1].split(' additional ')[0].strip()
                self.set_max_and_pts_from_line(additional_models_str, option, pts)
            if option.startswith("This Model may be replaced with"):
                additional_models_str = option.split("may be replaced with ")[1]
                words = additional_models_str.split(" ")
                model_name = " ".join(words[1:])  # Split off the number 1
                profile = self.get_profile_for_name(model_name)
                if profile is None:
                    continue
                profile.pts = pts
                profile.max = 1
                profile.min = 0
                if len(self.model_profiles) == 2:
                    for other_profile in self.model_profiles:
                        if profile == other_profile:
                            continue
                        other_profile.min = 0
                        other_profile.max = 1
                        self.errors.append(f"Needs replace by constraints and default set to {other_profile.name}")

    def process_hh3_special_rules(self):
        special_rules_list = self.subheadings.pop("SPECIAL RULES")
        special_rules_are_by_model = False
        for model in self.model_profiles:
            if model.name in special_rules_list:
                special_rules_are_by_model = True
                break

        special_rules_lines = special_rules_list.splitlines()
        if not special_rules_are_by_model:
            self.special_rules = split_at_dot(special_rules_lines)
            return

        # Order in the special rules list will not always be the same as in the profiles, so get the order.
        models_in_order = []
        for line in special_rules_lines:
            for model in self.model_profiles:
                if model.name == line:
                    models_in_order.append(model)

        for model in reversed(models_in_order):
            # print_styled(f"Splitting the following on {model.name}", STYLES.BLUE)
            # print(special_rules_list)
            _, special_rules_list, rules_for_model = split_at_header(model.name, special_rules_list)
            model.special_rules = split_at_dot(rules_for_model[len(model.name):].splitlines())
            # print(f"Set model special rules to {model.special_rules}")

    def process_hh2_subheadings(self):
        # Set the default with unit composition.
        if "Unit Composition" in self.subheadings:
            for line in split_at_dot(self.subheadings.pop("Unit Composition").splitlines()):
                self.set_default_composition_from_text_line(line)

        self.process_wargear("Wargear")

        # Going through all the options also gets us the points per model we wil use later.
        if "Options" in self.subheadings:
            option_groups_text = text_utils.un_justify(self.subheadings.pop("Options"), move_bullets=True)
            extra_special_options = ["Aspect Shrines", "Legiones Consularis", "Pater Consularis"]
            for extra_special_option in extra_special_options:
                if extra_special_option in option_groups_text:
                    index = option_groups_text.index(extra_special_option)
                    option_groups_text = option_groups_text[:index]
                    self.errors.append("This unit has an extra special option not yet handled.")
                    break
            # print_styled(option_groups_text, STYLES.PURPLE)
            for line in split_at_dot(option_groups_text.splitlines()):
                self.process_option_group(line)

        if "Special Rules" in self.subheadings:
            self.special_rules = split_at_dot(self.subheadings.pop("Special Rules").splitlines())

            new_page_dict = dict(self.page.special_rules_dict)  # To avoid modifying the dict while iterating through
            for special_rule_name, text in self.page.special_rules_dict.items():
                if special_rule_name in self.special_rules:
                    new_page_dict.pop(special_rule_name)  # Move from the page to this unit
                    if special_rule_name.startswith("Warlord: "):
                        warlord_trait_name = special_rule_name.split("Warlord: ")[1]
                        self.warlord_traits[warlord_trait_name] = text
                        self.special_rules.remove(special_rule_name)  # Move from special rules to warlord traits
                    else:  # Don't add warlord traits to the page special rules
                        self.special_rule_descriptions[special_rule_name] = text
            self.page.special_rules_dict = new_page_dict

        if "Unit Type" in self.subheadings:
            for line in split_at_dot(self.subheadings.pop("Unit Type").splitlines()):
                self.process_unit_types(line)

    def set_default_composition_from_text_line(self, line):
        line = line.strip()
        # print(line)
        first_space = line.index(' ')
        default_number = int(line[:first_space])
        model_name = line[first_space:].strip()
        model_profile = self.get_profile_for_name(model_name)
        if model_profile is not None:
            model_profile.min = default_number
            model_profile.max = default_number

    def process_wargear(self, wargear_subheading):
        if wargear_subheading in self.subheadings:
            for model in self.model_profiles:
                for line in split_at_dot(self.subheadings[wargear_subheading].splitlines()):
                    if "only)" in line:
                        if model.name not in line:
                            continue
                        line = line.split("(")[0].strip()
                    model.original_wargear.append(line)
                    model.default_wargear.append(line)

                # Check the special rules list for wargear in case it's not in the system.
                # To avoid modifying the dict while iterating through
                new_page_dict = dict(self.page.special_rules_dict)
                for special_rule_name, text in self.page.special_rules_dict.items():
                    if special_rule_name in model.original_wargear:
                        new_page_dict.pop(special_rule_name)  # Move from the page to this unit
                        model.wargear_descriptions[special_rule_name] = text
                self.page.special_rules_dict = new_page_dict
                for weapon in filter(lambda x: x.name in model.original_wargear, self.page_weapons):
                    model.wargear_profiles.append(weapon)
            self.subheadings.pop(wargear_subheading)

    def get_profile_for_name(self, model_name):
        if model_name.endswith("*"):
            model_name = model_name[:-1]
            self.errors.append(f"{model_name} has an asterisk! What does it mean?!?")
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
                self.errors.append(error_message)
                # raise Exception(error_message)
        return model_profile

    def process_option_group(self, line, do_not_apply_error=False):
        if ":" not in line:
            if not do_not_apply_error:
                self.errors.append(f"{line} is not an option group, there could be invisible text on the page")
            return
        first_colon = line.index(":")
        option_title = line[:first_colon] + ":"
        options = split_at_dash(line[first_colon + 1:])
        # print(option_title)

        # This is an "additional models" line, not relevant for hh3.
        if "may include" in option_title or ("may take" in option_title and "additional" in line):
            for option in options:
                name, pts = option_process_line(option)  # set points, don't do anything with entries
                if name.startswith("up to"):
                    additional_models_str = name.split('up to')[1].split('additional')[0].strip()
                    self.set_max_and_pts_from_line(additional_models_str, name, pts)
            return  # this section was points per model options, so we don't need to generate an options group.

        from_wargear_list, option_group, option_models, options = self.setup_option_group(option_title, options)
        defaulted_message = ", default (from wargear list)" if from_wargear_list else ""

        # Read name and points from the source text
        for option in options:
            # print("Option:", option)
            if option.strip() == "":
                continue
            name, pts = option_process_line(option)
            if line.endswith(" each"):
                self.errors.append(f"The option '{name}' may need a 'multiply by number of models' modifier")
            # print(f"\t\t{name} for {pts} pts{defaulted_message}")
            defaulted_message = ""  # Clear our defaulted message now that we've shown it.
            option_group.options.append(Option(name=name, pts=pts))

        for model in option_models:
            model.option_groups.append(option_group)
        if len(option_models) == 0 and len(option_group.options):
            self.option_groups.append(option_group)
        return True

    def setup_option_group(self, option_title, options):
        option_group = OptionGroup(title=option_title)
        option_group.max = 1
        if "and/or" in option_title or "up to two" in option_title:
            option_group.max = 2
        if "Up to two" in option_title and "in this unit may each" in option_title:
            option_group.max_shared = True
            self.errors.append(f"Shared on model level not yet implemented for {option_title}")

        option_models = []  # Temporary list of models that this option group applies to.
        # TODO: Handle one model name in another #33
        for model in self.model_profiles:
            model_name = model.name
            if "this model" in option_title.lower():
                option_models.append(model)
            if "any model" in option_title.lower() or model_name in option_title:
                if option_title.startswith("One"):
                    option_group.max_shared = True
                    self.errors.append(f"Shared on model level not yet implemented for {option_title}")
                # If the option is a "One model may" we leave this on the unit
                option_models.append(model)
        # if len(option_models) > 0:
        # print(f"\tApplies to {', '.join([model.name for model in option_models])}")
        from_wargear_list = False  # If the first entry is from the wargear list, and thus the default
        if "exchange" in option_title:
            # For wargear that gets exchanged, remove it from the default wargear, and add it to this list.
            add_to_options_list = []
            for model in option_models:
                wargear_removed_by_this_option = []
                for wargear in model.original_wargear:
                    # Default wargear shouldn't have 'and' in it, so we can pull straight from the list.
                    if wargear.lower() in option_title.lower():
                        wargear_removed_by_this_option.append(wargear)
                for wargear in wargear_removed_by_this_option:
                    if wargear not in model.default_wargear:
                        self.errors.append(
                            f"{wargear} is in two option lists for {model.name}, you will need to combine "
                            f"them by hand.")
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
        return from_wargear_list, option_group, option_models, options

    def set_max_and_pts_from_line(self, additional_models_str, name, pts):
        if "additional " in additional_models_str:
            model_name = name.split('additional ')[1]
        else:
            words = additional_models_str.split(" ")
            additional_models_str = words[0]
            model_name = " ".join(words[1:])
        if additional_models_str.isdigit():
            additional_models = int(additional_models_str)
        else:
            additional_models = text_utils.number_word_to_int(additional_models_str)
        # print(f"{model_name} x{additional_models} at {pts} each")
        profile = self.get_profile_for_name(model_name)
        if profile is None:
            return
        profile.pts = pts
        if profile.max is None:
            profile.max = 0  # Start at 0 if these models aren't necessarily additional.
        profile.max += additional_models
        if profile.min:
            # Reduce the points cost of the unit by the cost of each required model
            self.points -= (profile.pts * profile.min)

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
