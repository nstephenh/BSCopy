import argparse

from system.node import Node
from system.system import System
from xml.etree import ElementTree as ET

from util.element_util import get_description
from util.log_util import print_styled, STYLES, get_diff, prompt_y_n

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="Check system for duplicates and replace them with links")
    parser.add_argument("--interactive", '-i', action='store_true',
                        help="Prompt of special rules are identical")
    args = parser.parse_args()
    system = System('horus-heresy')
    duplicate_groups = system.get_duplicates()
    confirmed_duplicates = {}


    def add_to_confirmed_duplicates(group_name, new_node, match):
        """

        :param group_name:
        :param new_node: The node we just confirmed
        :param match: The node we confirmed against.
            If the confirmed duplicates group is being created, we need to add it as the first entry.
        :return:
        """
        if group_name not in confirmed_duplicates.keys():
            confirmed_duplicates[group_name] = [match]
        confirmed_duplicates[group_name].append(new_node)


    for group_name, nodes in duplicate_groups.items():
        print(f"{group_name} has {len(nodes) - 1} duplicates")
        rules_texts = {}
        hashes = {}
        for node in nodes:
            inside_text = "".join([ET.tostring(child, encoding='unicode') for child in node._element])
            fingerprint = hash(inside_text)
            rules_text = None
            if node.tag == 'rule':
                rules_text = node.get_description()
                fingerprint = hash(rules_text)

            print(f"\t{node.tag} {node._element.attrib['id']} in {node.system_file.name} with hash {fingerprint}")

            if fingerprint in hashes.keys():
                print(f"\t\tContents match exactly with {node._element.attrib['id']} in {node.system_file.name}")
                add_to_confirmed_duplicates(group_name, node, hashes[fingerprint])
            elif node.tag == 'rule':
                for comparison_text, comparison_node in rules_texts.items():
                    diff = get_diff(comparison_text, rules_text, 2)
                    if diff:
                        print_styled("\tText Differs!", STYLES.PURPLE)
                        print(diff)
                        if args.interactive and prompt_y_n("Do the above rules match?"):
                            add_to_confirmed_duplicates(group_name, node, comparison_node)
                    else:
                        print_styled("\tText close enough whitespace differences", STYLES.CYAN)
                        add_to_confirmed_duplicates(group_name, node, comparison_node)
                rules_texts[rules_text] = node
            hashes[fingerprint] = node

    addressed_count = 0
    total_count = 0
    link_update_count = 0

    for group_name, nodes in confirmed_duplicates.items():
        print_styled(f"{group_name} has {len(nodes) - 1} confirmed duplicates", STYLES.GREEN)
        best_option: 'Node' = nodes[0]  # First node
        for node in nodes:
            if node.system_file.is_gst:
                best_option = node
            # Factoring out is_gst and checking it first simplifies our best check below
            if best_option.system_file.is_gst:
                break  # Since there's only one GST, it'll always be the best option.
            if (best_option.system_file.library and node.system_file.library and
                    node.system_file.id in best_option.system_file.import_ids):
                best_option = node
                continue  # If both are libraries,
                # but best option is importing node, then node should be the best option.
            if (node.shared and not (best_option.shared or best_option.system_file.library)
                    or (node.system_file.library and not best_option.system_file.library)):
                best_option = node
        for node in nodes:
            is_best_option = "*" if node == best_option else " "
            print(f"\t{is_best_option} {node.tag} {node._element.attrib['id']} in {node.system_file.name}")

        for node in nodes:
            if node != best_option:
                total_count += 1
                if not (node.system_file == best_option.system_file
                        or best_option.system_file.is_gst
                        or (best_option.system_file.id in node.system_file.import_ids)):
                    print_styled(
                        f"\tCould not replace {node.tag} {node._element.attrib['id']} "
                        f"because {best_option.system_file.name} is not imported by {node.system_file.name}",
                        STYLES.RED)
                    continue
                children = []
                for child in node._element:
                    for tag in ['constraint', 'modifier']:
                        if tag in child.tag:
                            children.append(child)
                if len(children) > 0:
                    print_styled(
                        f"\tCould not replace {node.tag} {node._element.attrib['id']} "
                        f"because it would orphan the following: "
                        f"{[child.tag.split('}')[1] for child in children]}",
                        STYLES.RED)
                    continue
                addressed_count += 1
                print_styled(
                    f"\tReplacing {node.tag} {node._element.attrib['id']} with an entrylink to {best_option.id}",
                    style=STYLES.PURPLE)

                # Update all nodes pointing to this node.
                if node.id in system.nodes_by_target_id:
                    for link_node in system.nodes_by_target_id[node.id]:
                        link_node.set_target_id(best_option.id)
                        link_update_count += 1
                node.delete()
                grandparent = node.get_grandparent()
                info_link_section = grandparent.find(f"./{node.system_file.get_namespace_tag()}infoLinks")
                if not info_link_section:
                    info_link_section = ET.SubElement(grandparent,
                                                      f"{node.system_file.get_namespace_tag()}infoLinks")
                ET.SubElement(info_link_section, f"{node.system_file.get_namespace_tag()}infoLink", {
                    'id': node.id,
                    'name': best_option.name,
                    'targetId': best_option.id,
                    'type': node.tag
                })

    print(f"There are {len(duplicate_groups)} groups of duplicates")
    print(f"There were {len(confirmed_duplicates)} confirmed duplicate groups with {total_count} duplicates")
    print(f"{addressed_count} of which were addressed")
    print(f"{link_update_count} links were updated to point at the new best option")

    system.save_system()
