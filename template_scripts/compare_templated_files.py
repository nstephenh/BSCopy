import os

from system.system import System
from util.generate_util import get_identifier, ENTRY_LINK_TYPE
from xml.etree import ElementTree as ET

if __name__ == '__main__':

    system = System('horus-heresy')

    ET.register_namespace("", "http://www.battlescribe.net/schema/catalogueSchema")
    tree = ET.parse(os.path.expanduser('~/BattleScribe/data/horus-heresy/2022 - LA Template.cat'))

    template_nodes = {}
    nontemplate_nodes_by_target = {}

    # Find the base parts of the template
    template_file = list(filter(lambda x: x.is_template, system.files))[0]

    for node in template_file.all_nodes.filter(lambda x: x.is_base_level and x.tag == "entryLink"):
        bs_id = node.id
        name = str(node)
        template_nodes[bs_id] = {"Name": name,
                                 "Files": [],
                                 "Original Node": node,
                                 }
    missing_nodes = []
    for file in filter(lambda x: not x.is_template, system.files):
        print(file.name)
        for node in file.all_nodes.filter(lambda x: x.template_id and x.tag == "entryLink"):
            if node.template_id not in template_nodes:
                print(f"{node} is not in the template!")
                missing_nodes.append(node.template_id)
                continue
            if file.name not in template_nodes[node.template_id]["Files"]:
                template_nodes[node.template_id]["Files"].append(file.name)
                target_node = template_nodes[node.template_id]["Original Node"]
                # TODO: Compare target_node and node
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
