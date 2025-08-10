from system.system import System

if __name__ == '__main__':

    system = System('horus-heresy-3rd-edition')

    # for category_link in system.nodes_with_ids.filter(lambda x: x.type == "categoryLink"):
    for parent_force in system.gst.root_node.get_child("forceEntries").children:
        print(parent_force)
        if parent_force.get_child("forceEntries") is None:
            continue
        for child_force in parent_force.get_child("forceEntries").children:
            print("\t",child_force)
            if child_force.get_child("categoryLinks") is None:
                continue
            for category_link in child_force.get_child("categoryLinks").children:
                print("\t","\t",category_link)
                if not category_link.target_name.startswith("Prime "):
                    continue
                constraints = category_link.get_child("constraints")
                if constraints is None:
                    print("\t","\t","\t","Expected constraint")
                    continue
                if len(constraints.children) > 1:
                    print("\t","\t","\t","Expected only one constraint")
                    continue
                constraint = constraints.children[0]

                if "includeChildSelections" not in constraint.attrib.keys():
                    print("\t","\t","\t","Expected includeChildSelections")
                    constraint.update_attributes({"includeChildSelections": True})

    system.save_system()
