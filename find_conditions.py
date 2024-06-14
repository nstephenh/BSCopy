
from system.constants import SystemSettingsKeys, GameImportSpecs
from system.node_collection import NodeCollection
from system.system import System


if __name__ == '__main__':
    system = System('horus-heresy',
                    settings={
                        SystemSettingsKeys.GAME_IMPORT_SPEC: GameImportSpecs.HERESY,
                    },
                    )
    # get a list of all LA
    legion_ids = []
    blackshields_id = None
    legion_root = system.all_nodes.get(lambda x: x.id == "4a48-4935-246d-0c2e")
    for legion_node in NodeCollection(legion_root.children).get(lambda x: x.tag == "selectionEntries").children:
        if legion_node.name == "Blackshields":
            blackshields_id = legion_node.id
        else:
            legion_ids.append(legion_node.id)
    if blackshields_id is None:
        print("Could not find the ID for Blackshields, exiting")
        exit()
    print(f"Found {len(legion_ids)} Legions, and Blackshields in the Legions Selection Entry Group")

    all_modifiers = NodeCollection([])

    all_conditions_referencing_legions = system.all_nodes.filter(lambda x: x.tag == "condition" and x.condition_search_id in legion_ids)
    print(f"There are {len(all_conditions_referencing_legions)} conditions referencing legion Ids")
    for condition in all_conditions_referencing_legions:
        modifier = condition.find_ancestor_with(lambda x: x.tag == "modifier")
        if modifier not in all_modifiers:
            all_modifiers.append(modifier)

    print(f"There are {len(all_modifiers)} modifiers using those conditions")
    for modifier in all_modifiers:
        print(modifier)
        print(modifier.pretty_full())

