import re

from settings import fast_attack_force_org
from util.system_util import read_system
from util.system_globals import category_list
from util.text_gen_utils import option_group_gen_se, rules_list_to_infolinks, get_entrylink, errors
from util.text_utils import remove_plural, split_at_dot, split_at_dash, option_process_line, cleanup_disallowed_bs_characters
from util.generate_util import get_random_bs_id

page_number = "23"
publication_id = "89c5-118c-61fb-e6d8"

force_org = fast_attack_force_org

base_points = 160

access_points = ""  # Not adding automatic handling for this.

raw_text = """
PTERAXII SKYHUNTER COHORT
Pteraxii Skyhunter 7 4 4 4 4 2 4 2 7 4+
Pteraxii Alpha 7 4 4 4 4 2 4 3 8 4+

Unit Composition
● 4 Pteraxii Skyhunter
● 1 Pteraxii Alpha
Unit Type
● Pteraxii Skyhunter: Infantry (Skitarii)
● Pteraxii Alpha: Infantry
(Skitarii, Character)
Wargear
● Sicarian Battle Armour
● Scapuli-Pattern Thruster Pack
● Flechette Carbine
● Frag Grenades
Special Rules
● Relentless
● Deep Strike
● Hit & Run
● Thermal Riders
Options:
● A Pteraxii Skyhunter Cohort may include:
- Up to 5 additional Pteraxii Skyhunters.....................................................+25 points per model
● One Pteraxii Skyhunter may take a:
- Omnispex ...........................................................................................................................+5 points
● One Pteraxii Skyhunter may take a:
- Enhanced Data-Tether .....................................................................................................+5 points
● The unit may be equipped with any of the following:
- Arc Grenades ....................................................................................................................+30 points
- Pteraxii Talons .................................................................................................................+30 points
● Any model in the unit may exchange their Flechette Carbine for one of the following:
- Taser Goad and Flechette Blaster ...................................................................................+5 points
- Phosphor Torch .................................................................................................................+5 points
- Power Sword and Flechette Blaster.............................................................................. +15 points
- Transonic Blade and Flechette Blaster........................................................................ +20 points
- Two Transonic Blades .................................................................................................... +25 points
● The Pteraxii Alpha may take one of the following:
- Radium Pistol.....................................................................................................................+2 points
- Taser Goad..........................................................................................................................+5 points
- Phosphor Blast Pistol......................................................................................................+10 points
- Arc Pistol...........................................................................................................................+10 points
"""

output_file = "unit_output.xml"

final_output = ""

read_system()

raw_text = cleanup_disallowed_bs_characters(raw_text)

lines = [entry.strip() for entry in raw_text.split("\n") if entry.strip() != ""]
composition_index = lines.index("Unit Composition")
type_index = lines.index("Unit Type")
wargear_index = lines.index("Wargear")
try:
    special_rules_index = lines.index("Special Rules")
except Exception:
    special_rules_index = -1
options_index = lines.index("Options:")

composition_lines = lines[composition_index + 1:type_index]
unit_type_lines = lines[type_index + 1:wargear_index]
if special_rules_index != -1:
    wargear_lines = lines[wargear_index + 1:special_rules_index]
    rules_lines = lines[special_rules_index + 1:options_index]

else:
    wargear_lines = lines[wargear_index + 1:options_index]
    rules_lines = []
options_lines = lines[options_index + 1:]

unit_name = lines[0].title()

unit_stat_lines = lines[1:composition_index]

stats_dict = {}
cost_per_model = {}

model_min = {}
model_max = {}

UNIT = "UNIT"  # constant used for per-model dictionaries, options that apply to the unit.

for line in unit_stat_lines:
    first_digit = re.search('\d', line)
    if first_digit:
        stats_start = first_digit.start()
    else:
        raise Exception("Could not find first digit")

    model_name = line[:stats_start].strip()

    stats = line[stats_start:].strip().split(" ")
    stats_dict[model_name] = stats

for line in split_at_dot(composition_lines):
    first_space = line.index(' ')
    default_number = int(line[:first_space])
    model_name = remove_plural(line[first_space:].strip())
    model_min[model_name] = default_number
    model_max[model_name] = default_number

models = stats_dict.keys()

options_by_model = {UNIT: ""}  # model_name: string of SEGs

original_wargear_by_model = {}  # dictionary of option text
default_wargear_by_model = {}  # dictionary of option text
for model in models:
    original_wargear_by_model[model] = []
    default_wargear_by_model[model] = []
    options_by_model[model] = ""
    for line in split_at_dot(wargear_lines):
        original_wargear_by_model[model].append(line)
        default_wargear_by_model[model].append(line)

# Going through all the options also gets us the points per model we wil use later.
for line in split_at_dot(options_lines):
    this_option_lines = split_at_dash(line)
    option_title = this_option_lines[0]
    options = this_option_lines[1:]
    print(option_title)

    if "may include" in option_title:  # This is an "additional models" line
        for option in options:
            print("\t", option)
            name, pts = option_process_line(option)  # set points, don't do anything with entries
            if name.startswith("Up to"):
                additional_models = int(name.split('Up to')[1].split('additional')[0].strip())
                model_name = remove_plural(name.split('additional ')[1])
                print(f"{model_name} x{additional_models} at {pts} each")
                cost_per_model[model_name] = pts
                model_max[model_name] = model_max[model_name] + additional_models
        continue  # this section was points per model options, so we don't need to generate an options group.

    max_amount = 1
    if "and/or" in option_title:
        max_amount = 2

    option_models = []

    for model in models:
        if "Any model" in option_title or \
                (not option_title.startswith("One") and model in option_title):
            # If the option is a "One model may" we leave this on the
            option_models.append(model)
    if len(option_models) > 0:
        print(f"\t\tApplies to {', '.join(option_models)}")

    from_wargear_list = False  # If the first entry is from the wargear list, and thus the default

    if "exchange" in option_title:
        # For wargear that gets exchanged, remove it from the default wargear, and add it to this list.
        add_to_options_list = []
        for model in option_models:
            wargear_removed_by_this_option = []
            for wargear in original_wargear_by_model[model]:
                # Default wargear shouldn't have and in it, so we can pull straight from the list.
                if wargear in option_title:
                    wargear_removed_by_this_option.append(wargear)
            for wargear in wargear_removed_by_this_option:
                if wargear not in default_wargear_by_model[model]:
                    errors += f"{wargear} is in two option lists for {model}, you will need to combine them by hand \n"
                    continue  # We can't remove it from the list because we already have
                default_wargear_by_model[model].remove(wargear)
                if wargear not in add_to_options_list:  # To ensure we don't add it to our shared list twice.
                    add_to_options_list.append(wargear)
        for option in add_to_options_list:
            options = [option + " ... "] + options  # It'll be listed as free in the options list for that dropdown
            from_wargear_list = True  # use this to set the default

    option_tuples = []
    defaulted_message = ", default (from wargear list)" if from_wargear_list else ""

    # Read name and points from the source text
    for option in options:
        name, pts = option_process_line(option)
        if line.endswith(" each"):
            errors += f"The option '{name}' may need a 'multiply by number of models' modifier"
        print(f"\t{name} for {pts} pts{defaulted_message}")
        defaulted_message = ""  # Clear our defaulted message now that we've shown it.
        option_tuples.append((name, pts))

    if len(option_models) == 0:
        option_models.append(UNIT)  # options for the unit to ensure the per model loop runs.
    # per-model loop is needed to ensure each entry gets a unique ID
    for model in option_models:
        default_per_model = from_wargear_list
        selection_entries = ""
        links = ""
        for name, pts in option_tuples:
            if "&" in name or "and" in name:
                selection_entries += option_group_gen_se(name, pts,
                                                         default=default_per_model,
                                                         max_amount=max_amount)
            else:
                links += get_entrylink(name, pts, default=default_per_model, max_amount=max_amount)
            if default_per_model:
                default_per_model = False  # we've set the default now
        seg = f"""
                <selectionEntryGroup name="{option_title}" hidden="false" id="{get_random_bs_id()}">
                  <entryLinks>{links}
                  </entryLinks>
                  <selectionEntries>{selection_entries}
                  </selectionEntries>
                  <constraints>
                    <constraint type="min" value="0" field="selections" scope="parent" shared="true" id="{get_random_bs_id()}"/>
                    <constraint type="max" value="{max_amount}" field="selections" scope="parent" shared="true" id="{get_random_bs_id()}"/>
                  </constraints>
                </selectionEntryGroup>"""
        options_by_model[model] += seg

wargear_by_model = {}  # model_name: string of SEGs
for model in models:
    wargear_by_model[model] = ""
    # Add remaining wargear that hasn't been moved to an options group.
    print(f"Default wargear for {model}")
    for wargear in default_wargear_by_model[model]:
        print(f"\t{wargear}")
        wargear_by_model[model] += get_entrylink(wargear, only=True)

# Calculate the cost per the unit if there were none of the models that cost x pts per
remaining_points = base_points
for model_name in cost_per_model:
    remaining_points = remaining_points - (model_min[model_name] * cost_per_model[model_name])

# Put those points on the first singular model in the unit.
if remaining_points > 0 and len(cost_per_model) < len(model_min):
    for model_name in model_max:
        if model_max[model_name] == 1:
            cost_per_model[model_name] = remaining_points
            break

model_entries = ""
for line in split_at_dot(unit_type_lines):
    if ":" in line:
        model_name = line.split(":")[0].strip()
        unit_type_text = line.split(":")[1].strip()
    else:
        # Should be only one model

        model_name = list(stats_dict.keys())[0]
        unit_type_text = line.strip()
    unit_subtypes = []
    print(unit_type_text)
    if "(" in unit_type_text:
        unit_type = unit_type_text.split("(")[0].strip()
        unit_subtypes = unit_type_text.split("(")[1][:-1].strip().split(",")
    else:
        unit_type = unit_type_text
    category_links = ""
    for category in [unit_type] + unit_subtypes:
        category = category.strip()
        category_links += f"""
            <categoryLink targetId="{category_list[category]}" id="{get_random_bs_id()}" primary="false" />"""  # Not setting tne name node, will be set when bs saves
    stats = stats_dict[model_name]
    if len(stats) > 8:
        profile = f"""
            <profile name="{model_name}" typeId="4bb2-cb95-e6c8-5a21" typeName="Unit" hidden="false" id="{get_random_bs_id()}" publicationId="{publication_id}" page="{page_number}">
              <characteristics>
                <characteristic name="Unit Type" typeId="ddd7-6f5c-a939-b69e">{unit_type_text}</characteristic>
                <characteristic name="Move" typeId="893e-2d76-8f04-44e5">{stats[0]}</characteristic>
                <characteristic name="WS" typeId="cc42-7ed5-7092-5c84">{stats[1]}</characteristic>
                <characteristic name="BS" typeId="74ae-c840-0036-d244">{stats[2]}</characteristic>
                <characteristic name="S" typeId="e478-41d4-a092-48a8">{stats[3]}</characteristic>
                <characteristic name="T" typeId="c32b-5fdd-3fbe-9b1f">{stats[4]}</characteristic>
                <characteristic name="W" typeId="57ee-1126-32a9-5672">{stats[5]}</characteristic>
                <characteristic name="I" typeId="62d3-22d7-2d49-52dc">{stats[6]}</characteristic>
                <characteristic name="A" typeId="f111-2ce5-dd12-d6b0">{stats[7]}</characteristic>
                <characteristic name="Ld" typeId="e8a6-1da9-d384-8727">{stats[8]}</characteristic>
                <characteristic name="Save" typeId="e593-6b3c-f169-04f0">{stats[9]}</characteristic>
              </characteristics>
            </profile>
"""
    else:
        if len(stats) == 6:
            stats.append("-")  # Empty Transport capacity got stripped out, so add it back in
        profile = f"""
            <profile name="{model_name}" typeId="2fae-b053-3f78-e7b2" typeName="Vehicle" hidden="false" id="{get_random_bs_id()}" publicationId="{publication_id}" page="{page_number}">
              <characteristics>
                <characteristic name="Unit Type" typeId="e555-4aed-dfcc-c0b4">{unit_type_text}</characteristic>
                <characteristic name="Move" typeId="3614-4a2d-bffb-90e4">{stats[0]}</characteristic>
                <characteristic name="BS" typeId="51fb-b7d9-aa59-863d">{stats[1]}</characteristic>
                <characteristic name="Front" typeId="0ef8-a648-01d0-08ee">{stats[2]}</characteristic>
                <characteristic name="Side" typeId="f150-c0dc-c192-9cb3">{stats[3]}</characteristic>
                <characteristic name="Rear" typeId="8d4e-2aea-fffc-d556">{stats[4]}</characteristic>
                <characteristic name="HP" typeId="a76c-83b1-602f-9e62">{stats[5]}</characteristic>
                <characteristic name="Transport Capacity" typeId="0c90-79e2-f768-e547">{stats[6]}</characteristic>
                <characteristic name="Access Points" typeId="e217-1b1e-9494-3e3e">{access_points}</characteristic>
              </characteristics>
            </profile>
"""
    model_options = ""
    if model_name in options_by_model:
        options_and_wargear = wargear_by_model[model_name] + options_by_model[model_name]
        model_options = f"""
      <selectionEntryGroups>
        {options_and_wargear}
      </selectionEntryGroups>
        """
    model = f"""
        <selectionEntry type="model" import="true" name="{model_name}" hidden="false" id="{get_random_bs_id()}" publicationId="{publication_id}" page="{page_number}">
          <profiles>
             {profile}
          </profiles>
          <constraints>
            <constraint type="min" value="{model_min[model_name]}" field="selections" scope="parent" shared="true" id="{get_random_bs_id()}"/>
            <constraint type="max" value="{model_max[model_name]}" field="selections" scope="parent" shared="true" id="{get_random_bs_id()}"/>
          </constraints>
          <costs>
            <cost name="Pts" typeId="d2ee-04cb-5f8a-2642" value="{cost_per_model[model_name]}"/>
          </costs>
          <categoryLinks>{category_links}
          </categoryLinks>
          {model_options}
        </selectionEntry>"""
    model_entries += model

rules_links = rules_list_to_infolinks(split_at_dot(rules_lines))

output = f"""
    <selectionEntry type="unit" import="true" name="{unit_name}" hidden="false" id="{get_random_bs_id()}" publicationId="{publication_id}" page="{page_number}">
      <selectionEntries>
        {model_entries}
      </selectionEntries>
      <categoryLinks>
        <categoryLink id="98ca-4c49-4f7e-b8a7" name="Unit:" hidden="false" targetId="36c3-e85e-97cc-c503" primary="false"/>
        {force_org}
      </categoryLinks>
      <selectionEntryGroups>
        {options_by_model[UNIT]}
      </selectionEntryGroups>
      {rules_links}
    </selectionEntry>
"""
if len(errors) > 1:
    print("There were one or more errors, please validate output")
    print(errors)
f = open(output_file, "a")
f.write(output)
f.close()
