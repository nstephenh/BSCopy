from text_utils import read_rules_from_system, read_wargear_from_system, rules_list_to_infolinks
from util import get_random_bs_id, SHARED_RULES_TYPE, SELECTION_ENTRY_TYPE

page_number = "32"
publication_id = "89c5-118c-61fb-e6d8"

base_points = 110

raw_text = """
SKITARII VANGUARD COHORT

Skitarii Vanguard 7 3 4 3 3 1 3 1 7 4+
Vanguard Alpha 7 3 4 3 3 2 3 2 8 4+

Unit Composition
● 9 Skitarii Vanguard
● 1 Vanguard Alpha
Unit Type
● Skitarii Vanguard: Infantry
(Skitarii, Line)
● Vanguard Alpha: Infantry
(Skitarii, Character, Line)
Wargear
● Corpus Skitarii
● Radium Carbine
● Frag Grenades
Special Rules
● Rad-Saturation

Options:
● A Skitarii Vanguard Cohort may include:
- Up to 20 additional Skitarii Vanguard ....................................................... +8 points per model
● One Skitarii Vanguard may take a:
- Augury Scanner ...............................................................................................................+10 points
● One Skitarii Vanguard may take a:
- Nuncio Vox.......................................................................................................................+10 points
● One Skitarii Vanguard may take a:
- Omnispex ...........................................................................................................................+5 points
● One Skitarii Vanguard may take a:
- Enhanced Data-Tether .....................................................................................................+5 points
● The Vanguard Alpha may take one of the following:
- Taser Goad..........................................................................................................................+5 points
- Arc Maul..............................................................................................................................+5 points
- Power Weapon.................................................................................................................+10 points
- Transonic Razor...............................................................................................................+10 points
- Power Fist......................................................................................................................... +15 points
● The Vanguard Alpha may take one of the following:
- Radium Pistol.....................................................................................................................+2 points
- Phosphor Blast Pistol......................................................................................................+10 points
- Arc Pistol...........................................................................................................................+10 points
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
    bullet_entries = line.split("- ")
    return [entry.strip() for entry in bullet_entries if entry.strip() != ""]


def get_entrylink(name, pts=None):
    global hasError, errors, wargear_list
    if name in wargear_list:
        wargear_id = wargear_list[name]
        link_text = f'entryLink import="true" name="{name}" hidden="false" type="selectionEntry" id="{get_random_bs_id()}" targetId="{wargear_id}"'
        if pts:
            return f"""        <{link_text}>
          <constraints>
            <constraint type="max" value="1" field="selections" scope="parent" shared="true" id="{get_random_bs_id()}"/>
          </constraints>
          <costs>
            <cost name="Pts" typeId="d2ee-04cb-5f8a-2642" value="{pts}"/>
          </costs>
        </entryLink>"""
        else:
            return f"<{link_text} />"
    else:
        hasError = True
        errors = errors + f"Could not find wargear for: {name}\n"
    return ""


def option_get_link(line):
    """
    Call before models on unit are set.
    :param line:
    :return:
    """
    global cost_per_model, model_max
    name = line[:line.index('.')].strip()
    pts_string = line[line.index('+') + 1:]
    pts = int(pts_string[:pts_string.index(' ')])
    if name.startswith("Up to"):
        additional_models = int(name.split('Up to')[1].split('additional')[0].strip())
        model_name = name.split('additional ')[1]
        print(f"{model_name} x{additional_models} at {pts} each")
        cost_per_model[model_name] = pts
        model_max[model_name] = additional_models
        pass
    else:
        return get_entrylink(name, pts=pts)


unit_stat_lines = lines[1:composition_index]

stats_dict = {}

for line in unit_stat_lines:
    model_name = line[:-21]
    stats = line[-21:].strip().split(" ")
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
            option_get_link(option)  # set points, don't do anything with entries
        continue  # this is only for links.

    if "may take a" in option_title:
        pass
        # min 0 max 1
    if "may take one of" in option_title:
        pass
        # min 0 max 1

    links = ""
    for option in options:
        print("\t", option)
        links = links + option_get_link(option)
    print(links)
    print("find me")
    seg = f"""            <selectionEntryGroup name="{option_title}" hidden="false" id="{get_random_bs_id()}">
              <entryLinks>{links}
              </entryLinks>
              <constraints>
                <constraint type="min" value="{0}" field="selections" scope="parent" shared="true" id="{get_random_bs_id()}"/>
                <constraint type="max" value="{1}" field="selections" scope="parent" shared="true" id="{get_random_bs_id()}"/>
              </constraints>
            </selectionEntryGroup>"""
    options_output = options_output + seg

for line in split_at_dot(composition_lines):
    first_space = line.index(' ')
    default_number = int(line[:first_space])
    model_name = line[first_space:].strip()
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

print(cost_per_model)  # for our test case of 110 - 8*9 , should be 38 for the sgt

for line in split_at_dot(unit_type_lines):
    model_name = line.split(":")[0].strip()
    unit_type_text = line.split(":")[1].strip()
    stats = stats_dict[model_name]
    model = f"""
        <selectionEntry type="model" import="true" name="{model_name}" hidden="false" id="{get_random_bs_id()}" page="{page_number}">
          <profiles>
            <profile name="{model_name}" typeId="4bb2-cb95-e6c8-5a21" typeName="Unit" hidden="false" id="{get_random_bs_id()}">
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
    wargear_links += get_entrylink(line)

rules_links = rules_list_to_infolinks(split_at_dot(rules_lines), rules_list)

output = f"""
    <selectionEntry type="unit" import="true" name="{unit_name}" hidden="false" id="{get_random_bs_id()}">
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
print(output)
if (hasError):
    print("There were one or more errors, please validate the above")
    print(errors)
f = open(output_file, "a")
f.write(output)
f.close()
