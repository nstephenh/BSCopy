import re
import uuid
import xml.etree.ElementTree as ET

COMMENT_NODE_TYPE = "{http://www.battlescribe.net/schema/catalogueSchema}comment"
SELECTION_ENTRY_TYPE = '{http://www.battlescribe.net/schema/catalogueSchema}selectionEntry'
ENTRY_LINK_TYPE = '{http://www.battlescribe.net/schema/catalogueSchema}entryLink'
MODIFIER_TYPE = '{http://www.battlescribe.net/schema/catalogueSchema}modifier'
CONDITION_TYPE = '{http://www.battlescribe.net/schema/catalogueSchema}condition'
CONDITION_GROUP_TYPE = '{http://www.battlescribe.net/schema/catalogueSchema}conditionGroup'
SELECTION_ENTRY_GROUP_TYPE = '{http://www.battlescribe.net/schema/catalogueSchema}selectionEntryGroup'
SHARED_SELECTION_ENTRY_GROUPS_TYPE = '{http://www.battlescribe.net/schema/catalogueSchema}sharedSelectionEntryGroups'
SHARED_RULES_TYPE = '{http://www.battlescribe.net/schema/catalogueSchema}sharedRules'

BS_NAMESPACES = ['{http://www.battlescribe.net/schema/catalogueSchema}',
                 '{http://www.battlescribe.net/schema/gameSystemSchema}']


def get_random_bs_id():
    return str(uuid.uuid4())[4:23]


def get_identifier(node):
    name = node.attrib.get("name")
    hidden = node.attrib.get("hidden")
    return "{}_{}_hidden_{}".format(name, node.tag, hidden)


def comment(attribute_name, bs_id):
    return "template_{}_{}".format(attribute_name, bs_id)


def comment_id(bs_id):
    return "node_id_{}".format(bs_id)


def make_comment(node_to_modify, attribute_name, source_id, overwrite=False):
    comment_node = get_or_make_comment_node(node_to_modify)
    new_comment_text = comment(attribute_name, source_id)
    try:
        comment_tag = comment(attribute_name, "")
        id_start = comment_node.text.index(comment_tag)
        if overwrite:  # Update existing comment if it exists
            comment_node.text = comment_node.text[:id_start] + new_comment_text
    except ValueError:
        # Only append comment if comment does not already exist
        comment_node.text += "    {}".format(new_comment_text)


def get_or_make_comment_node(node_to_modify):
    comment_node = node_to_modify.find(COMMENT_NODE_TYPE)
    if comment_node is None:
        comment_node = ET.SubElement(node_to_modify, COMMENT_NODE_TYPE)
        comment_node.text = ""
    return comment_node


def give_comment_id(node_to_modify, bs_id):
    comment_node = get_or_make_comment_node(node_to_modify)
    try:
        comment_node.text.index(comment_id(bs_id))
    except ValueError:
        # Only append comment if comment does not already exist
        comment_node.text += "    {}".format(comment_id(bs_id))


def find_comment_value(node, attribute_name="id", node_id=False):
    """
    Finds the attribute_name or the node_id
    :param node:
    :param attribute_name:
    :param node_id:
    :return:
    """
    comment_node = node.find(COMMENT_NODE_TYPE)
    if comment_node is not None:
        try:
            comment_tag = comment(attribute_name, "")
            if node_id:
                comment_tag = comment_id("")
            id_start = comment_node.text.index(comment_tag) + len(comment_tag)
            return comment_node.text[id_start:id_start + 20]
        except ValueError:
            pass


def add_new_id(node_map, source_node):
    """
    Queues up a change for a copy of this node.
    Adds the source ID to the list of IDs to change
    :param node_map:
    :param source_node:
    :return:
    """
    bs_id = source_node.attrib.get("id")
    if not bs_id:
        bs_id = find_comment_value(source_node, node_id=True)
    if bs_id and bs_id not in node_map.keys():
        node_map[bs_id] = get_random_bs_id()


def update_tag(node_map, node, attribute_name, generate_map_comments=True):
    """
    Updates tags on node based on node_map
    :param node_map:
    :param node:
    :param attribute_name:
    :param generate_map_comments:
    :return:
    """
    bs_id = node.attrib.get(attribute_name)
    if bs_id and bs_id in node_map.keys():
        # Don't copy if map comment already exists.
        if find_comment_value(node, attribute_name) is None:
            node.attrib[attribute_name] = node_map[bs_id]
            if generate_map_comments:
                make_comment(node, attribute_name, bs_id)


def update_all_node_ids(nodes, node_map, generate_map_comments=True, assign_ids_to_mods_and_cons=False):
    for node in nodes:
        update_tag(node_map, node, "id", generate_map_comments)
        update_tag(node_map, node, "targetId", generate_map_comments)
        update_tag(node_map, node, 'scope', generate_map_comments)
        update_tag(node_map, node, 'childId', generate_map_comments)
        update_tag(node_map, node, 'field', generate_map_comments)
        # If we are assigning IDs to mods and cons, they can get random IDs
        if assign_ids_to_mods_and_cons and \
                node.tag in [MODIFIER_TYPE, CONDITION_TYPE, CONDITION_GROUP_TYPE]:
            give_comment_id(node, get_random_bs_id())


def get_mod_and_con_ids(nodes):
    ids = []
    for node in nodes:
        if node.tag in [MODIFIER_TYPE, CONDITION_TYPE, CONDITION_GROUP_TYPE]:
            node_id = find_comment_value(node, node_id=True)
            if node_id:
                ids.append(node_id)
    return ids


def cleanup_file_match_bs_whitespace(filepath):
    content = ""
    in_tag = False
    with open(filepath, 'r', encoding="utf-8") as f:
        content = f.read()
        content = re.sub(' />', '/>', content)  # BS leaves out this space, so we need to replace them all
        # The XML parser leaves apostrophes and quotes, see issue: https://github.com/python/cpython/issues/72086
        # We have to handle them ourselves
        # We could use beautiful soup for this, but I'm attempting to avoid imports.
        # That is also the reason we're not mocking _escape_cdata
        content = re.sub("'", "&apos;", content)
        # Go through and find all the quotes not inside of tags.
        new_content = ""
        for char in content:
            if char == "<" and not in_tag:
                in_tag = True
            elif char == ">" and in_tag:
                in_tag = False
            elif char in ["<", ">"]:
                raise Exception("This method didn't work, a < or > was encountered unexpectedly")
            if not in_tag and char == '"':
                char = "&quot;"
            new_content += char
        content = new_content

    with open(filepath, 'w', encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n')  # Files start with this line always
        f.write(content)
        f.write('\n')  # Newline at end of file
