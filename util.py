import uuid
import xml.etree.ElementTree as ET

COMMENT_NODE_TYPE = "{http://www.battlescribe.net/schema/catalogueSchema}comment"


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
        comment_node.text += "\n {}".format(comment(attribute_name, source_id))
