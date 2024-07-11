from util.system_util import read_system
from util.text_gen_utils import rules_list_to_infolinks, errors
from util.generate_util import get_random_bs_id

page_number = "96"
publication_id = "89c5-118c-61fb-e6d8"
raw_text = """
Three Word Name 12-96“ 7 5 Heavy 5, Barrage, Blast (3”), Pinning, Rending (5+)
Regular Name 24“ 5 4 Rapid Fire, Ignores Cover
Regular Name 24“ 5 4 Rapid Fire 2, Ignores Cover
shortname - +3 - Melee, Overload (6+), Sudden Strike (3)
"""

output_file = "weapon_output.xml"
final_output = ""


def get_name(component_list):
    # if len(component_list) == 1:
    #     return component_list[0]
    return " ".join(component_list)


read_system()
hasError = False

for line in raw_text.split("\n"):
    line = line.strip()
    if line == "":
        continue
    first_half = line.split(",")[0].split(" ")
    type_or_num = first_half[-1]
    offset = 0

    try:
        num = int(type_or_num)  # Type is not melee or rapid fire
        weapon_type = " ".join(first_half[-2:])
        offset = 1
    except Exception:
        weapon_type = first_half[-1]

    if first_half[-1] == "Fire":
        weapon_type = "Rapid Fire"
        offset = 1

    if first_half[-2] == "Fire":  # "Rapid Fire 2"
        weapon_type = "Rapid " + weapon_type
        offset = 2

    # Type is melee
    ap = first_half[-2 - offset]
    str = first_half[-3 - offset]
    range = first_half[-4 - offset]
    weapon_name = get_name(first_half[:-4 - offset])
    range = range

    print(line)
    print("\t", "w: {} r: {} s: {} ap: {} type: {}".format(
        weapon_name, range, str, ap, weapon_type
    ))

    type_and_srs = line[line.index(weapon_type):]

    weapon_rules = type_and_srs.split(',')[1:]
    rules_output = rules_list_to_infolinks(weapon_rules)

    root_id = get_random_bs_id()
    output = f""" <selectionEntry type="upgrade" import="true" name="{weapon_name}" hidden="false" id="{get_random_bs_id()}" publicationId="{publication_id}" page="{page_number}">
        <profiles>
        <profile name="{weapon_name}" typeId="1a1a-e592-2849-a5c0" typeName="Weapon" hidden="false" id="{get_random_bs_id()}" publicationId="{publication_id}" page="{page_number}">
          <characteristics>
            <characteristic name="Range" typeId="95ba-cda7-b831-6066">{range}</characteristic>
            <characteristic name="Strength" typeId="24d9-b8e1-a355-2458">{str}</characteristic>
            <characteristic name="AP" typeId="f7a6-e0d8-7973-cd8d">{ap}</characteristic>
            <characteristic name="Type" typeId="2f86-c8b4-b3b4-3ff9">{type_and_srs}</characteristic>
          </characteristics>
        </profile>
        </profiles>
        {rules_output}
    </selectionEntry>"""
    final_output += "\n" + output

if len(errors) > 1:
    print("There were one or more errors, please validate the output")
    print(errors)

f = open(output_file, "a")
f.write(final_output)
f.close()
