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

    search_count = 0
    updated_modifiers = []

    modifier: 'Node'  # Type hint
    for modifier in needs_review:
        # modifier.parent is "modifiers", modifier.parent.parent is whatever is actually getting modified.
        if (not modifier.parent.parent.is_wargear_link) and (
                (modifier.value == "true" and modifier.type_name == "set")
        ):
            print("Looks like it's not a wargear modifier")
            print(modifier)
            print(modifier.pretty_full())
            search_count += 1
            # continue  # Quit early without doing anything

            print("Moving the condition to an 'or' group")
            existing_conditions = modifier.get_child("conditions")
            condition_groups = modifier.get_or_create_child("conditionGroups")
            if condition_groups.get_child("conditionGroup", attrib={"type": "and"}):
                print("Handling for moving a condition group of type 'and' not yet implemented\n")
                # TODO: move existing condition groups
                continue

            group = condition_groups.get_or_create_child("conditionGroup", attrib={"type": "or"})
            if existing_conditions:  # There may not be any exisiting condtions if they were already in a condition group
                # Should existing conditions should be moved into an "and" group?
                group.move_node_to_here(existing_conditions)

            conditions = group.get_or_create_child("conditions")
            print("Adding a blackshield condition")
            # Only use the below condition for "set hidden = true" modifiers
            conditions.get_or_create_child("condition", attrib={"type": "equalTo",
                                                                "value": "1",
                                                                "field": "selections",
                                                                "scope": "force",
                                                                "childId": blackshields_id,  # "ae4a-f95c-968e-eb46",
                                                                "shared": "true",
                                                                "includeChildSelections": "true"})
            print("Result:")
            print(modifier.pretty_full())
            updated_modifiers.append(modifier)
    print("\n\n----------------")
    print(f"There are {len(all_modifiers)} modifiers using those conditions")
    print(f"{len(reference_blackshields)} modifiers already reference blackshields")
    print(f"{len(needs_review)} need review")
    print(f"{search_count} of those match our search condition")
    system.save_system()
    print(f"{len(updated_modifiers)} conditions updated this run:")
    for mod in updated_modifiers:
        print(mod)
