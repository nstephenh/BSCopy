from collections import Counter

from system.system import System
from util.generate_util import get_random_bs_id


def get_duplicate_counts(my_list):
    counts = Counter(my_list)
    return {item: count for item, count in counts.items() if count > 1}


if __name__ == '__main__':
    system = System('horus-heresy-3rd-edition')

    id_list = []
    for node in system.nodes_with_ids:
        id_list.append(node.id)

    duplicates = get_duplicate_counts(id_list)
    duplicate_sets = []
    for node_id in duplicates.keys():
        original_node = None
        for count, node in enumerate(system.nodes_with_ids.filter(lambda x: x.id == node_id)):
            if count == 0:
                original_node = node
                print(f"{node}")
                continue
            if original_node.parent == node.parent:
                print(f"\tDeleting likely duplicate {node}")
                node.delete()
            else:
                node.attrib.update({"id": get_random_bs_id()})
                print(f"\tGenerating new ID for {node}")

    system.save_system()
