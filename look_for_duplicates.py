from system.system import System
from xml.etree import ElementTree as ET

from util.log_util import print_styled, STYLES

if __name__ == '__main__':
    system = System('horus-heresy')
    duplicate_groups = system.get_duplicates()
    confirmed_duplicates = {}
    for group_name, nodes in duplicate_groups.items():
        print(f"{group_name} has {len(nodes) - 1} duplicates")
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

    addressed_count = 0
    total_count = 0

    for group_name, nodes in confirmed_duplicates.items():
        print_styled(f"{group_name} has {len(nodes) - 1} confirmed duplicates", STYLES.GREEN)
        best_option = nodes[0]  # First node
        for node in nodes:
            if ((node.shared and not best_option.shared)
                    or (node.system_file.library and not best_option.system_file.library)
                    or (node.system_file.is_gst and not best_option.system_file.is_gst)):
                best_option = node
        for node in nodes:
            is_best_option = "*" if node == best_option else " "
            print(f"\t{is_best_option} {node.tag} {node.element.attrib['id']} in {node.system_file.name}")

        for node in nodes:
            if node != best_option:
                total_count += 1
                if (node.system_file != best_option.system_file) and not best_option.system_file.is_gst:
                    print_styled(
                        f"\tCould not replace {node.tag} {node.element.attrib['id']} "
                        f"because we're not sure it's imported in the target",
                        STYLES.RED)
                    continue
                addressed_count += 1
                print_styled(
                    f"\tReplacing {node.tag} {node.element.attrib['id']} with an entrylink to {best_option.id}",
                    style=STYLES.PURPLE)
                grandparent = node.get_grandparent()
                node.delete()
                links = grandparent.find(f"./{node.system_file.get_namespace_tag()}infoLinks")
                if not links:
                    links = ET.SubElement(grandparent, f"{node.system_file.get_namespace_tag()}infoLinks", {})
                ET.SubElement(links, f"{node.system_file.get_namespace_tag()}infoLink", {
                    'id': node.id,
                    'name': best_option.name,
                    'targetId': best_option.id,
                    'type': node.tag
                })

    print(f"There are {len(duplicate_groups)} groups of duplicates")
    print(f"There were {len(confirmed_duplicates)} confirmed duplicate groups with {total_count} duplicates")
    print(f"{addressed_count} of which were addressed")

    system.save_system()
