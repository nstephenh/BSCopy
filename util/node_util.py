from typing import TYPE_CHECKING

from util.log_util import print_styled

from xml.etree import ElementTree as ET

if TYPE_CHECKING:
    from system.system_file import SystemFile


class NodeUtil:

    def __init__(self, system_file: 'SystemFile', element: ET.Element):
        self.system_file = system_file
        self.element = element
        self.id = element.attrib.get('id')
        self.tag = element.tag
        print(self.tag)
        if not self.id:
            raise Exception("Node initialization attempted on element with no ID")


def get_description(node):
    if not node:
        return None
    for child in node:
        if child.tag.endswith('description'):
            return child
    return None


def update_page_and_pub(node, page, publication_id):
    if 'page' not in node.attrib or node.attrib['page'] != page:
        print_styled("\tUpdated page number")
        node.attrib['page'] = page
    if 'publicationId' not in node.attrib or node.attrib['publicationId'] != publication_id:
        print_styled("\tUpdated publication ID")
        node.attrib['publicationId'] = publication_id
