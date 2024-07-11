import os

from system.system import System
from util.generate_util import get_identifier, ENTRY_LINK_TYPE
from xml.etree import ElementTree as ET

if __name__ == '__main__':

    system = System('horus-heresy')

    ET.register_namespace("", "http://www.battlescribe.net/schema/catalogueSchema")
    tree = ET.parse(os.path.expanduser('~/BattleScribe/data/horus-heresy/2022 - LA Template.cattemplate'))

    template_nodes = {}
    nontemplate_nodes_by_target = {}

    # Find the base parts of the template
    for node in tree.findall("./{}s/{}".format(ENTRY_LINK_TYPE, ENTRY_LINK_TYPE)):
        bs_id = node.attrib.get("id")
        name = node.attrib.get("name")
        template_nodes[bs_id] = {"Name": name,
                                 "Files": []
                                 }
    missing_nodes = []
    for file in system.files:
        print(file.name)
        for node in file.all_nodes.filter(lambda x: x.template_id):
            if node.template_id not in template_nodes:
                print(f"{node.template_id} is expected to be in template, but missing!")
                missing_nodes.append(node.template_id)
                continue
            if file.name not in template_nodes[node.template_id]["Files"]:
                template_nodes[node.template_id]["Files"].append(file.name)
            else:
                print(f"{template_nodes[node.template_id]['Name']} appears at least twice in {file.name}")

        for node in file.all_nodes.filter(lambda x: ((not x.template_id)
                                                     and x.is_base_level
                                                     and x.tag == "entryLink")
                                          ):
            if node.target_id not in nontemplate_nodes_by_target:
                nontemplate_nodes_by_target[node.target_id] = {
                    "Name": node.target_name,
                    "Files": [],
                    "Nodes": []
                }
            nontemplate_nodes_by_target[node.target_id]["Nodes"].append(node)
            if file.name not in nontemplate_nodes_by_target[node.target_id]["Files"]:
                nontemplate_nodes_by_target[node.target_id]["Files"].append(file.name)
            else:
                print(f"{node} appears at least twice in {file.name}")

    print("Existing Templated nodes:")
    for template_id, properties in template_nodes.items():
        print(f"\t{properties['Name']}: {len(properties['Files'])}")

    print("Non-template nodes sorted by number of references:")
    nontemplate_nodes_by_target = {k: v for k, v in sorted(nontemplate_nodes_by_target.items(),
                                                           key=lambda item: len(item[1]["Nodes"]))}
    for target_id, properties in nontemplate_nodes_by_target.items():
        print(f"\t{properties['Name']}: {len(properties['Files'])}")
