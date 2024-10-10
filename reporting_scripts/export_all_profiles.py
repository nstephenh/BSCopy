import json
import sys

from system.system import System

if __name__ == '__main__':
    system_name = "horus-heresy"

    try:
        system_name = sys.argv[1]
    except IndexError:
        pass

    system = System(system_name)

    json_export = {}

    json_export["Publications"] = []
    for publication_node in system.nodes_with_ids.filter(lambda node: node.tag == 'publication'):
        json_export["Publications"].append({
            "Name": publication_node.name,
            "Builder ID": publication_node.id,
            "Publication Date": publication_node.attrib.get("publicationDate"),
        })

    json_export["Profile Types"] = []
    for profile_type, profile_id in system.profile_types.items():
        characteristics = []
        for characteristic, characteristic_id in system.profile_characteristics[profile_type].items():
            characteristics.append({
                "Name": characteristic,
                "Builder ID": characteristic_id,
            })
        json_export["Profile Types"].append({
            "Name": profile_type,
            "Builder ID": profile_id,
            "Characteristics": characteristics,
        })

    json_export["Profiles"] = []
    for profile_node in system.nodes_with_ids.filter(lambda node: node.tag == 'profile'):
        profile_dict = profile_node.get_profile_dict()
        profile_dict["Type"] = profile_node.type_name
        profile_dict["Builder ID"] = profile_node.id
        profile_dict["Publication ID"] = profile_node.pub
        profile_dict["Page"] = profile_node.page
        print(profile_dict)
        json_export["Profiles"].append(profile_dict)

    json_export["Rules"] = []
    for rule_node in system.nodes_with_ids.filter(lambda node: node.tag == 'rule'):
        rule_dict = {
            "Name": rule_node.name,
            "Text": rule_node.get_rules_text(),
            "Builder ID": rule_node.id,
            "Publication ID": rule_node.pub,
            "Page": rule_node.page,
        }
        print(rule_dict)
        json_export["Rules"].append(rule_dict)

    with open(f'../exports/{system_name}_profiles.json', 'w') as outfile:
        json.dump(json_export, outfile, indent=2)
