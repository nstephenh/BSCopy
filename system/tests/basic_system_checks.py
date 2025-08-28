import json
import os
import unittest
from collections import Counter

from system.system import System


class BasicSystemTests(unittest.TestCase):

    def setUp(self):
        game_name = os.getenv("SYSTEM_NAME")
        self.assertIsNotNone(game_name, "Missing SYSTEM_NAME environment variable")
        self.system = System(game_name)

    def test_ids(self):
        system = self.system
        id_list = []
        for node in system.nodes_with_ids:
            id_list.append(node.id)

        with self.subTest("No Duplicate IDs"):
            duplicates = self.get_duplicate_counts(id_list)
            duplicate_sets = []
            for node_id, count in duplicates.items():
                duplicate_sets = {
                    f"{node_id} appears {count} times": [str(node) for node in
                                                         system.nodes_with_ids.filter(lambda x: x.id == node_id)]
                }
            self.assertTrue(len(duplicate_sets) == 0, "Duplicate IDs found: " + json.dumps(duplicate_sets, indent=2))

        for node in system.nodes_with_ids:
            if node.target_id:
                with self.subTest(f"Link validity on {node}"):
                    self.assertTrue(node.target_id in id_list,
                                    f"Link {node.attrib['name']} targets {node.target_id} which does not exist")

    @staticmethod
    def get_duplicate_counts(my_list):
        counts = Counter(my_list)
        return {item: count for item, count in counts.items() if count > 1}

    def test_link_names(self):
        system = self.system
        ids_to_names = {}
        for node in system.nodes_with_ids:
            ids_to_names[node.id] = node.name
        for node in system.nodes_with_ids:
            if node.target_id and node.target_id in ids_to_names.keys():
                with self.subTest(f"{node} should be named {ids_to_names[node.target_id]}"):
                    # Using node.attrib because we don't set node.name on links
                    self.assertEqual(node.attrib['name'], ids_to_names[node.target_id])


if __name__ == '__main__':
    unittest.main()
