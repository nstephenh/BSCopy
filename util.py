import uuid
import xml.etree.ElementTree as ET

COMMENT_NODE_TYPE = "{http://www.battlescribe.net/schema/catalogueSchema}comment"
SELECTION_ENTRY_TYPE ='{http://www.battlescribe.net/schema/catalogueSchema}selectionEntry'
ENTRY_LINK_TYPE ='{http://www.battlescribe.net/schema/catalogueSchema}entryLink'


def get_random_bs_id():
    return str(uuid.uuid4())[4:23]


def get_identifier(node):
    name = node.attrib.get("name")
    return "{}_{}".format(name, node.tag)


def comment(attribute_name, bs_id):
    return "library_{}_{}".format(attribute_name, bs_id)


def make_comment(node_to_modify, attribute_name, source_id):
    comment_node = node_to_modify.find(COMMENT_NODE_TYPE)
    if comment_node is None:
        comment_node = ET.SubElement(node_to_modify, COMMENT_NODE_TYPE)
        comment_node.text = ""
    try:
        comment_node.text.index(comment(attribute_name, source_id))
    except ValueError:
        # Only append comment if comment does not already exist
        comment_node.text += "    {}".format(comment(attribute_name, source_id))


def find_source_id(node):
    comment_node = node.find(COMMENT_NODE_TYPE)
    if comment_node is not None:
        try:
            comment_tag = comment("id", "")
            id_start = comment_node.text.index(comment_tag) + len(comment_tag)
            return comment_node.text[id_start:id_start + 20]
        except ValueError:
            pass
