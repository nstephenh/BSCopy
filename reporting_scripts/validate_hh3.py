import argparse

from system.constants import SystemSettingsKeys, GameImportSpecs
from system.node import Node
from system.system import System
from xml.etree import ElementTree as ET

from util.element_util import get_description
from util.log_util import print_styled, STYLES, get_diff, prompt_y_n

if __name__ == '__main__':

    system = System('horus-heresy-3rd-edition',
                    settings={
                        # SystemSettingsKeys.GAME_IMPORT_SPEC: GameImportSpecs.HERESY3E,
                    },
                    )
    for file in system.files:
        entry_links_node = file.root_node.get_child(tag='entryLinks')
        if entry_links_node is None:
            continue
        for child in entry_links_node.children:
            category_count = len(child.get_categories())
            if category_count != 1:
                print(f"{child} has {category_count} categories, only 1 is expected")

