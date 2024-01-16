from system.system import System
from xml.etree import ElementTree as ET

from util.log_util import print_styled, STYLES

if __name__ == '__main__':
    system = System('horus-heresy')
    duplicate_groups = system.get_duplicates()
    confirmed_duplicates = {}
    for group_name, nodes in duplicate_groups.items():
        print(f"{group_name} has {len(nodes)} duplicates")
        hashes = {}
        for node in nodes:
            inside_text = "".join([ET.tostring(child, encoding='unicode') for child in node.element])
            fingerprint = hash(inside_text)
            print(f"\t{node.tag} {node.element.attrib['id']} in {node.system_file.name} with hash {fingerprint}")
            if fingerprint in hashes.keys():
                print(f"\t\tMatches with {node.element.attrib['id']} in {node.system_file.name}")
                if group_name not in confirmed_duplicates.keys():
                    confirmed_duplicates[group_name] = [hashes[fingerprint]]
                confirmed_duplicates[group_name].append(node)
            hashes[fingerprint] = node
    for group_name, nodes in confirmed_duplicates.items():
        print_styled(f"{group_name} has {len(nodes)} confirmed duplicates", STYLES.GREEN)
        for node in nodes:
            print(f"\t{node.tag} {node.element.attrib['id']} in {node.system_file.name}")

    print(f"There are {len(duplicate_groups)} groups of duplicates")
    print(f"There are {len(confirmed_duplicates)} of which have confirmed duplicates")
