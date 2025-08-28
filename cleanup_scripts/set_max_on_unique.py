from system.constants import SystemSettingsKeys, GameImportSpecs
from system.node import Node
from system.system import System

if __name__ == '__main__':
    expected_attribs = {
        "type": "max",
        "value": "1",
        "field": "selections",
        "scope": "roster",
        "shared": "true",
        "includeChildSelections": "true",
        "includeChildForces": "true",
    }
    expected_attribs_with_no_include_child = expected_attribs.copy()
    expected_attribs_with_no_include_child.pop("includeChildForces")
    system = System('horus-heresy-3rd-edition',
                    settings={
                        SystemSettingsKeys.GAME_IMPORT_SPEC: GameImportSpecs.HERESY3E,
                    },
                    )
    for unique_type_link in system.nodes_with_ids.filter(lambda x:
                                                         x.tag == "categoryLink"
                                                         and x.target_name == "Unique Model Sub-Type"
                                                         ):
        unit = unique_type_link.find_ancestor_with(lambda x: x.type == "selectionEntry:unit")
        if unit is None:
            continue
        constraints = unit.get_or_create_child("constraints")
        if len(constraints.children) <= 1:
            max_constraint = constraints.get_or_create_child("constraint", {"type": "max"})
            max_constraint.attrib.update(expected_attribs)
            continue
        for constraint in constraints.children:
            copy_with_no_child_forces_or_id = constraint.attrib.copy()
            copy_with_no_child_forces_or_id.pop("id")
            copy_with_no_child_forces_or_id.pop("includeChildForces", None)
            if Node.are_attribs_equal(copy_with_no_child_forces_or_id, expected_attribs_with_no_include_child):
                # Update any existing that don't have includeChildForces.
                constraint.attrib.update({"includeChildForces": "true"})
                break

    system.save_system()
