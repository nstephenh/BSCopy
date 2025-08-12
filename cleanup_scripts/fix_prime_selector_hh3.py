from system.game.heresy3e import Heresy3e
from system.system import System
from util.generate_util import get_random_bs_id

if __name__ == '__main__':

    system = System('horus-heresy-3rd-edition')

    # for category_link in system.nodes_with_ids.filter(lambda x: x.type == "categoryLink"):
    battlefield_roles = Heresy3e.BATTLEFIELD_ROLES.copy()

    # Warlords aren't ever prime? High command can be in EC.
    battlefield_roles.remove("Warlord")
    # Lords of war are only prime in knights, make a separate test for this.
    battlefield_roles.remove("Lord of War")

    # First, get all units
    unit_ids = []
    for file in system.files:
        entry_links_node = file.root_node.get_child(tag='entryLinks')
        if entry_links_node is None:
            continue
        for child in entry_links_node.children:
            category_links = child.get_child(tag='categoryLinks')
            primary_cat = category_links.get_child(tag='categoryLink', attrib={"primary": "true"})
            if primary_cat.target_name in battlefield_roles:
                unit_ids.append(child.target_id)
    for unit_id in unit_ids:
        unit = system.get_node_by_id(unit_id)
        entry_links = unit.get_or_create_child("entryLinks")
        prime_link = entry_links.get_child(tag='entryLink',
                                           attrib={'targetId': '3fa2-78b1-637f-7fb2'})  # Prime Unit ID
        created_prime_link = False
        if prime_link is None:
            prime_link = entry_links.get_or_create_child(tag='entryLink',
                                                         attrib={'import': 'true',
                                                                 'name': 'Prime Unit',
                                                                 'hidden': 'false',
                                                                 'id': get_random_bs_id(),
                                                                 'type': 'selectionEntry',
                                                                 'targetId': '3fa2-78b1-637f-7fb2'})  # Prime Unit ID
            created_prime_link = True

        prime_benefit_links = prime_link.get_or_create_child("entryLinks")

        prime_selector_id = Heresy3e().get_prime_selector(unit.system_file.faction)
        if prime_selector_id is None:
            continue
        faction_benefits_list = prime_benefit_links.get_child(tag='entryLink',
                                                          attrib={  # GST Prime Benefits
                                                              'targetId': prime_selector_id
                                                          })
        if faction_benefits_list is None:
            faction_benefits_list = prime_benefit_links.get_or_create_child(tag='entryLink',
                                                                        attrib={'import': 'true',
                                                                                'name': 'Prime Benefits',
                                                                                'hidden': 'false',
                                                                                'id': get_random_bs_id(),
                                                                                'type': 'selectionEntryGroup',
                                                                                'targetId': prime_selector_id})

    system.save_system()
