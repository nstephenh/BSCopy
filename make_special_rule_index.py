import argparse
import csv

from book_reader.raw_entry import RawModel
from system.constants import SystemSettingsKeys, GameImportSpecs
from system.node import Node
from system.system import System
from xml.etree import ElementTree as ET

from util.element_util import get_description
from util.log_util import print_styled, STYLES, get_diff, prompt_y_n

if __name__ == '__main__':

    system = System('horus-heresy-panoptica',
                    settings={
                        SystemSettingsKeys.GAME_IMPORT_SPEC: GameImportSpecs.HERESY,
                    },
                    )

    publication_names = {}
    for node in system.gst.root_node.get_child("publications").children:
        publication_names[node.id] = node.name

    with open('exports/rules.csv', 'w', newline="") as csvfile:

        writer = csv.DictWriter(csvfile, fieldnames=["name", "page", "publication"])
        writer.writeheader()

        for rule in system.nodes_with_ids.filter(lambda x: x.type == "rule"):
            if rule.name is None:
                continue  # Not sure why there's some blanks here, maybe links are being counted?
            rule_as_dict = {
                "name": rule.name,
                "page": rule.attrib.get('page'),
            }
            pub = rule.attrib.get('publicationId')
            if pub is not None:
                rule_as_dict["publication"] = publication_names[pub]
            writer.writerow(rule_as_dict)

    with open('exports/wargear.csv', 'w', newline="") as csvfile:

        writer = csv.DictWriter(csvfile, fieldnames=["name", "page", "publication"])
        writer.writeheader()

        for rule in system.nodes_with_ids.filter(lambda x: x.type == "profile:Wargear Item"):
            if rule.name is None:
                continue  # Not sure why there's some blanks here, maybe links are being counted?
            rule_as_dict = {
                "name": rule.name,
                "page": rule.attrib.get('page'),
            }
            pub = rule.attrib.get('publicationId')
            if pub is not None:
                rule_as_dict["publication"] = publication_names[pub]
            writer.writerow(rule_as_dict)

    with open('exports/weapons.csv', 'w', newline="") as csvfile:

        writer = csv.DictWriter(csvfile, fieldnames=["name", "page", "publication"])
        writer.writeheader()

        for rule in system.nodes_with_ids.filter(lambda x: x.type == "profile:Weapon"):
            if rule.name is None:
                continue  # Not sure why there's some blanks here, maybe links are being counted?
            rule_as_dict = {
                "name": rule.name,
                "page": rule.attrib.get('page'),
            }
            pub = rule.attrib.get('publicationId')
            if pub is not None:
                rule_as_dict["publication"] = publication_names[pub]
            writer.writerow(rule_as_dict)