import argparse

from book_reader.raw_entry import RawModel
from system.constants import SystemSettingsKeys, GameImportSpecs
from system.node import Node
from system.system import System
from xml.etree import ElementTree as ET

from util.element_util import get_description
from util.log_util import print_styled, STYLES, get_diff, prompt_y_n

if __name__ == '__main__':

    system = System('horus-heresy',
                    settings={
                        SystemSettingsKeys.GAME_IMPORT_SPEC: GameImportSpecs.HERESY2E,
                    },
                    )
    category_a = "Vehicle"
    category_b = "Vehicle Unit"

    category_a_id = system.categories[category_a].id
    category_b_id = system.categories[category_b].id

    nodes_a_and_b = []
    nodes_a_only = []
    nodes_b_only = []
    for node in system.nodes_with_ids.filter(lambda x: True):
        categories = node.get_categories()
        if categories is None:
            continue
        if category_a_id in categories and category_b_id in categories:
            nodes_a_and_b.append(node)
        if category_a_id in categories and category_b_id not in categories:
            nodes_a_only.append(node)
        if category_a_id not in categories and category_b_id in categories:
            nodes_b_only.append(node)

    total = len(nodes_a_and_b) + len(nodes_a_only) + len(nodes_b_only)
    print(f"Total referencing {category_a} and/or {category_b} : {total}")
    print(f"{category_a} and {category_b}: {len(nodes_a_and_b)}")
    for node in nodes_a_and_b:
        print("\t", node)
    print(f"{category_a} only: {len(nodes_a_only)}")
    for node in nodes_a_only:
        print("\t", node)
    print(f"{category_b} only: {len(nodes_b_only)}")
    for node in nodes_b_only:
        print("\t", node)

