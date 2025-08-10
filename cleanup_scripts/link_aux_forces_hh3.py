from system.system import System
from util.generate_util import get_random_bs_id

if __name__ == '__main__':

    system = System('horus-heresy-3rd-edition')

    crusade = system.get_node_by_id("8562-592c-8d4b-a1f0")
    allied_links = system.get_node_by_id("256b-b8a8-017a-75e9").get_child("forceEntryLinks")
    for child_force in crusade.get_child("forceEntries").children:
        print("\t", child_force)
        if not child_force.name.startswith("Auxiliary - "):
            continue
        if allied_links.get_child("forceEntryLink", attrib={"targetId": child_force.id}) is not None:
            continue
        allied_links.get_or_create_child("forceEntryLink",
                                         attrib={"name": child_force.name,
                                                 "id": get_random_bs_id(),
                                                 "hidden": "false",
                                                 "targetId": child_force.id,
                                                 "type": "forceEntry"
                                                 }
                                         )

    system.save_system()
