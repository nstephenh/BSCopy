import os
import xml.etree.ElementTree as ET

from util.generate_util import make_comment, get_identifier, ENTRY_LINK_TYPE, SELECTION_ENTRY_GROUP_TYPE, \
    SHARED_SELECTION_ENTRY_GROUPS_TYPE


def get_sseg_named(tree, name):
    return tree.find("./{}/{}[@name='{}']".
                     format(SHARED_SELECTION_ENTRY_GROUPS_TYPE, SELECTION_ENTRY_GROUP_TYPE, name))


# Press the green button in the gutter to run the script.
if __name__ == '__main__':

    name_map = {}  # Dictionary of names to input_ids
    ET.register_namespace("", "http://www.battlescribe.net/schema/catalogueSchema")
    tree = ET.parse(os.path.expanduser('~/BattleScribe/data/horus-heresy/2022 - LA Template.cattemplate'))

    # Find the base parts of the template
    for node in tree.findall("./{}s/{}".format(ENTRY_LINK_TYPE, ENTRY_LINK_TYPE)):
        bs_id = node.attrib.get("id")
        name = node.attrib.get("name")
        node_identifier = get_identifier(node)
        if name and bs_id:
            if node_identifier in name_map:
                print("{} needs manually mapped due to multiple entries".format(name))
            name_map[node_identifier] = bs_id

    retinue_id = get_sseg_named(tree, "Retinue").attrib.get("id")
    warlord_id = get_sseg_named(tree, "Warlord Traits").attrib.get("id")

    base_path = os.path.expanduser('~/BattleScribe/data/horus-heresy')
    la_files = os.listdir(base_path)

    for file_name in la_files:
        if file_name.startswith("2022 - LA - "):
            file_path = os.path.join(base_path, file_name)
            tree = ET.parse(file_path)
            for node in tree.findall("./{}s/{}".format(ENTRY_LINK_TYPE, ENTRY_LINK_TYPE)):
                bs_id = node.attrib.get("id")
                name = node.attrib.get("name")
                identifier = get_identifier(node)
                if name and bs_id and (identifier in name_map.keys()):
                    make_comment(node, "id", name_map[identifier], overwrite=True)
            retinue_node = get_sseg_named(tree, "Retinue")
            make_comment(retinue_node, "id", retinue_id, overwrite=True)
            warlord_node = get_sseg_named(tree, "Warlord Traits")
            make_comment(warlord_node, "id", warlord_id, overwrite=True)
            tree.write(file_path)
