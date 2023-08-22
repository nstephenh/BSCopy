from text_utils import read_rules_from_system, read_wargear_from_system, rules_list_to_infolinks
from util import get_random_bs_id, SHARED_RULES_TYPE, SELECTION_ENTRY_TYPE

page_number = "35"
publication_id = "89c5-118c-61fb-e6d8"

base_points = 140

raw_text = """
ELECTRO-PRIEST CONCLAVE
Electro-Priest 7 4 3 3 3 1 4 2 8 -

Unit Composition
● 10 Electro-Priests
Unit Type
● Infantry
Wargear
● Voltagheist Field
● Frag Grenades
Special Rules
● Hatred (Everything!)
● Feel No Pain (5+)
● Support Squad

Options:
● An Electro-Priest Conclave may include:
- Up to 10 additional Electro-Priests............................................................+14 points per model
● The entire squad must select one of the following options
(all models in the unit must take the same option):
- Electrostatic Gauntlets & Corpuscarii Electoo..................................................................... Free
- Electroleech Stave & Fulgurite Electoo.................................................................................. Free
"""

output_file = "unit_output.xml"
final_output = ""

hasError = False
errors = ""
rules_list = read_rules_from_system()
wargear_list = read_wargear_from_system()

lines = [entry.strip() for entry in raw_text.split("\n") if entry.strip() != ""]
composition_index = lines.index("Unit Composition")
type_index = lines.index("Unit Type")
wargear_index = lines.index("Wargear")
special_rules_index = lines.index("Special Rules")
options_index = lines.index("Options:")

composition_lines = lines[composition_index + 1:type_index]
unit_type_lines = lines[type_index + 1:wargear_index]
wargear_lines = lines[wargear_index + 1:special_rules_index]
rules_lines = lines[special_rules_index + 1:options_index]
options_lines = lines[options_index + 1:]

unit_name = lines[0].title()


def split_at_dot(lines):
    """
    Given an entry split at line breaks containing bullet points, combine and split at bullet points
    :param lines:
    :return:
    """
    space_string = " ".join(lines)
    bullet_entries = space_string.split("● ")
    return [entry.strip() for entry in bullet_entries if entry.strip() != ""]


def split_at_dash(line):
    print("Split at dash this: ", line)
    dash_entries = line.split("- ")
    return [entry.strip() for entry in dash_entries if entry.strip() != ""]


def remove_plural(model_name):
    if model_name.endswith('s'):
        model_name = model_name[:-1]
    return model_name


name_synonyms = {
    "Corpus Skitarii": "The Corpus Skitarii",
    "Nuncio Vox": "Nuncio-Vox"
}


def check_alt_names(name):
    if name in name_synonyms:
        return name_synonyms[name]
    return name


def get_entrylink(name, pts=None, only=False):
    global hasError, errors, wargear_list
    lookup_name = check_alt_names(name)
    if lookup_name in wargear_list:
        wargear_id = wargear_list[lookup_name]
        link_text = f'entryLink import="true" name="{name}" hidden="false" type="selectionEntry" id="{get_random_bs_id()}" targetId="{wargear_id}"'
        if pts:
            return f"""
        <{link_text}>
          <constraints>
            <constraint type="max" value="1" field="selections" scope="parent" shared="true" id="{get_random_bs_id()}"/>
          </constraints>
          <costs>
            <cost name="Pts" typeId="d2ee-04cb-5f8a-2642" value="{pts}"/>
          </costs>
        </entryLink>"""
        elif only:  # If the only/default option (wargear), then set it as min 1 max 1
            return f"""
        <{link_text}>
          <constraints>
            <constraint type="min" value="1" field="selections" scope="parent" shared="true" id="{get_random_bs_id()}"/>
            <constraint type="max" value="1" field="selections" scope="parent" shared="true" id="{get_random_bs_id()}"/>
          </constraints>
        </entryLink>"""
        else:
            return f"\n<{link_text} />"

    else:
        hasError = True
        errors = errors + f"Could not find wargear for: {name}\n"
    return ""


def option_get_se(name, pts):
    # When an option is a group of options and needs a SE containing multiple entry links.
    suboptions = ""
    for sub_option in name.split("&"):
        print(sub_option)
        suboptions = suboptions + get_entrylink(sub_option.strip(), only=True)
    return f"""
                      <selectionEntry type="upgrade" name="{name}" hidden="false" id="{get_random_bs_id()}">
                        <entryLinks>{suboptions}
                        </entryLinks>
                      </selectionEntry>"""


def option_get_link(name, pts):
    return get_entrylink(name, pts=pts)


def option_process_line(line):
    global cost_per_model, model_max
    name = line[:line.index('.')].strip()
    pts = 0
    try:
        pts_string = line[line.index('+') + 1:]
        pts = int(pts_string[:pts_string.index(' ')])
    except ValueError:
        pass  # Free
    if name.startswith("Up to"):
        additional_models = int(name.split('Up to')[1].split('additional')[0].strip())
        model_name = remove_plural(name.split('additional ')[1])
        print(f"{model_name} x{additional_models} at {pts} each")
        cost_per_model[model_name] = pts
        model_max[model_name] = additional_models
    else:
        return name, pts


unit_stat_lines = lines[1:composition_index]

stats_dict = {}

for line in unit_stat_lines:
    if not "+" in line:
        stats_length = 20
    else:
        stats_length = 21
    model_name = line[:-stats_length]

    stats = line[-stats_length:].strip().split(" ")
    stats_dict[model_name] = stats

models = ""

cost_per_model = {}

model_min = {}
model_max = {}

# Getting all the options also gets us the points per model we wil use later.
options_output = ""
for line in split_at_dot(options_lines):
    this_option_lines = split_at_dash(line)
    option_title = this_option_lines[0]
    options = this_option_lines[1:]
    print(option_title)
    if "may include" in option_title:
        for option in options:
            print("\t", option)
            option_process_line(option)  # set points, don't do anything with entries
        continue  # this is only for points per model options, skip processing options for this option group.

    links = ""
    selection_entries = ""
    for option in options:
        print("\t", option)
        name, pts = option_process_line(option)
        if name:  # If name isn't returned, it's instead getting points per model
            if "&" in name:
                selection_entries = selection_entries + option_get_se(name, pts)
            else:
                links = links + option_get_link(name, pts)
    seg = f"""
            <selectionEntryGroup name="{option_title}" hidden="false" id="{get_random_bs_id()}">
              <entryLinks>{links}
              </entryLinks>
              <selectionEntries>{selection_entries}
              </selectionEntries>
              <constraints>
                <constraint type="min" value="{0}" field="selections" scope="parent" shared="true" id="{get_random_bs_id()}"/>
                <constraint type="max" value="{1}" field="selections" scope="parent" shared="true" id="{get_random_bs_id()}"/>
              </constraints>
            </selectionEntryGroup>"""
    options_output = options_output + seg

for line in split_at_dot(composition_lines):
    first_space = line.index(' ')
    default_number = int(line[:first_space])
    model_name = remove_plural(line[first_space:].strip())
    model_min[model_name] = default_number
    if model_name not in model_max:
        model_max[model_name] = default_number
    else:
        model_max[model_name] = model_max[model_name] + default_number

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

for line in split_at_dot(unit_type_lines):
    if ":" in line:
        model_name = line.split(":")[0].strip()
        unit_type_text = line.split(":")[1].strip()
    else:
        # Should be only one model

        model_name = list(stats_dict.keys())[0]
        unit_type_text = line.strip()
    stats = stats_dict[model_name]
    model = f"""
        <selectionEntry type="model" import="true" name="{model_name}" hidden="false" id="{get_random_bs_id()}" publicationId="{publication_id}" page="{page_number}">
          <profiles>
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
          </profiles>
          <constraints>
            <constraint type="min" value="{model_min[model_name]}" field="selections" scope="parent" shared="true" id="{get_random_bs_id()}"/>
            <constraint type="max" value="{model_max[model_name]}" field="selections" scope="parent" shared="true" id="{get_random_bs_id()}"/>
          </constraints>
          <costs>
            <cost name="Pts" typeId="d2ee-04cb-5f8a-2642" value="{cost_per_model[model_name]}"/>
          </costs>
        </selectionEntry>"""
    models += model

wargear_links = ""

for line in split_at_dot(wargear_lines):
    wargear_links += get_entrylink(line, only=True)

rules_links = rules_list_to_infolinks(split_at_dot(rules_lines), rules_list)

output = f"""
    <selectionEntry type="unit" import="true" name="{unit_name}" hidden="false" id="{get_random_bs_id()}" publicationId="{publication_id}" page="{page_number}">
      <selectionEntries>{models}
      </selectionEntries>
      <categoryLinks>
        <categoryLink targetId="9b5d-fac7-799b-d7e7" id="{get_random_bs_id()}" primary="true" name="Troops:"/>
      </categoryLinks>
      <entryLinks>{wargear_links}
      </entryLinks>
      <selectionEntryGroups>{options_output}
      </selectionEntryGroups>
      {rules_links}
    </selectionEntry>
"""
if (hasError):
    print("There were one or more errors, please validate the above")
    print(errors)
f = open(output_file, "a")
f.write(output)
f.close()
