import os
import xml.etree.ElementTree as ET

from util import make_comment, get_identifier, ENTRY_LINK_TYPE

# Press the green button in the gutter to run the script.
if __name__ == '__main__':

    name_map = {}  # Dictionary of names to input_ids
    ET.register_namespace("", "http://www.battlescribe.net/schema/catalogueSchema")
    tree = ET.parse(os.path.expanduser('~/BattleScribe/data/horus-heresy/2022 - LA Template.cattemplate'))

    # Find the base parts of the template
    for node in tree.findall("./{}s/{}".format(ENTRY_LINK_TYPE, ENTRY_LINK_TYPE)):
        bs_id = node.attrib.get("id")
        name = node.attrib.get("name")
        if name and bs_id:
            name_map[get_identifier(node)] = bs_id
        if name and not bs_id:
            print("{} has name but no ID: {}".format(node, name))
        if bs_id and not name:
            print("{} has ID but no Name: {}".format(node, bs_id))

    base_path = os.path.expanduser('~/BattleScribe/data/horus-heresy')
    la_files = os.listdir(base_path)

    for file_name in la_files:
        if file_name.startswith("2022 - LA - "):
            file_path = os.path.join(base_path, file_name)
            tree2 = ET.parse(file_path)
            for node in tree2.findall("./{}s/{}".format(ENTRY_LINK_TYPE, ENTRY_LINK_TYPE)):
                bs_id = node.attrib.get("id")
                name = node.attrib.get("name")
                identifier = get_identifier(node)
                if name and bs_id and (identifier in name_map.keys()):
                    make_comment(node, "id", name_map[identifier])
            tree2.write(file_path)
