import argparse

from system.node import Node
from system.system import System
from xml.etree import ElementTree as ET

from util.element_util import get_description
from util.log_util import print_styled, STYLES, get_diff, prompt_y_n

if __name__ == '__main__':

    system = System('horus-heresy')

    ids_to_names = {}
    for node in system.nodes_with_ids:
        ids_to_names[node.id] = node.name
    for node in system.nodes_with_ids:
        if node.target_id:
            target_name = ids_to_names[node.target_id]
            node_name = node.attrib['name']
            if node_name is None:
                continue  # Skip nodes with no name.
            if node_name != target_name:
                print(f"Renaming {node_name} {node} to {target_name}")
                node.update_attributes({
                    'name': target_name
                })

    system.save_system()
