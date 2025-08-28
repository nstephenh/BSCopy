from system.constants import SystemSettingsKeys, GameImportSpecs
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


    system.save_system()
