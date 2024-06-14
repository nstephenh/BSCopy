from system.constants import SystemSettingsKeys, GameImportSpecs
from system.node import Node
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
    reference_blackshields = NodeCollection([])
    needs_review = NodeCollection([])

    all_conditions_referencing_legions = system.all_nodes.filter(
        lambda x: x.tag == "condition" and x.condition_search_id in legion_ids)
    print(f"There are {len(all_conditions_referencing_legions)} conditions referencing legion Ids")
    for condition in all_conditions_referencing_legions:
        modifier = condition.find_ancestor_with(lambda x: x.tag == "modifier")
        if modifier not in all_modifiers:
            all_modifiers.append(modifier)
            if modifier.does_descendent_exist(lambda x: x.condition_search_id == blackshields_id):
                reference_blackshields.append(modifier)
            else:
                needs_review.append(modifier)

    whitescars_count = 0
    modifier: 'Node'  # Type hint
    for modifier in needs_review:
        if modifier.field == "893e-2d76-8f04-44e5" and (
                (modifier.value == "*" and modifier.type_name == "append")
                or
                (modifier.value == "1" and modifier.type_name == "increment")
                or
                (modifier.value[-1] == "*" and modifier.type_name == "set")
        ):
            print("Looks like white scars move modifier")
            print(modifier)
            print(modifier.pretty_full())
            whitescars_count += 1
            if modifier.get_child("conditionGroups"):
                print("Not sure how to handle an existing conditonGroup, skipping")
                continue  # Not sure how to handle an existing group yet.

            print("Moving the condition to an 'and' group")
            existing_conditions = modifier.get_child("conditions")
            and_group = (modifier.get_or_create_child("conditionGroups").
                         get_or_create_child("conditionGroup", attrib={"type": "and"}))
            and_group.move_node_to_here(existing_conditions)
            conditions = and_group.get_child("conditions")
            print("Adding a blackshield condition")
            conditions.get_or_create_child("condition", attrib={"type": "equalTo",
                                                                "value": "0",
                                                                "field": "selections",
                                                                "scope": "force",
                                                                "childId": blackshields_id,  # "ae4a-f95c-968e-eb46",
                                                                "shared": "true",
                                                                "includeChildSelections": "true"})
            print("Result:")
            print(modifier.pretty_full())

    print(f"There are {len(all_modifiers)} modifiers using those conditions")
    print(f"{len(reference_blackshields)} modifiers already reference blackshields")
    print(f"{len(needs_review)} need review")
    print(f"{whitescars_count} of those appear to be whitescars movement")
    system.save_system()
