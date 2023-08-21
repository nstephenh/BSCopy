from text_utils import read_rules_from_system, read_wargear_from_system, rules_list_to_infolinks
from util import get_random_bs_id, SHARED_RULES_TYPE, SELECTION_ENTRY_TYPE

page_number = "32"
publication_id = "89c5-118c-61fb-e6d8"

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
special_rules = lines.index("Special Rules")

composition_lines = lines[composition_index + 1:type_index]
unit_type_lines = lines[type_index + 1:wargear_index]
wargear_lines = lines[wargear_index + 1:special_rules]
rules_lines = lines[special_rules + 1:]

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


unit_stat_lines = lines[1:composition_index]

stats_dict = {}

for line in unit_stat_lines:
    model_name = line[:-21]
    stats = line[-21:].strip().split(" ")
    stats_dict[model_name] = stats

models = ""

number_dict = {}

for line in split_at_dot(composition_lines):
    first_space = line.index(' ')
    default_number = line[:first_space]
    model_name = line[first_space:].strip()
    number_dict[model_name] = default_number

for line in split_at_dot(unit_type_lines):
    model_name = line.split(":")[0].strip()
    unit_type_text = line.split(":")[1].strip()
    stats = stats_dict[model_name]
    number = number_dict[model_name]
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
            <constraint type="min" value="{number}" field="selections" scope="parent" shared="true" id="{get_random_bs_id()}"/>
            <constraint type="max" value="{number}" field="selections" scope="parent" shared="true" id="{get_random_bs_id()}"/>
          </constraints>
        </selectionEntry>"""
    models += model

wargear_links = ""
for line in split_at_dot(wargear_lines):
    if line in wargear_list:
        wargear_id = wargear_list[line]
        wargear_links += f"""
        <entryLink import="true" name="{line}" hidden="false" type="selectionEntry" id="{get_random_bs_id()}" targetId="{wargear_id}"/>"""
    else:
        hasError = True
        errors = errors + f"Could not find wargear for: {line}\n"

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
