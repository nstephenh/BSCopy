from util.generate_util import get_random_bs_id
from util.log_util import print_styled
import xml.etree.ElementTree as ET


def get_description(element):
    if not element:
        return None
    for child in element:
        if child.tag.endswith('description'):
            return child
    return None


def update_page_and_pub(element, page, publication_id):
    if 'page' not in element.attrib or element.attrib['page'] != page:
        print_styled("\tUpdated page number")
        element.attrib['page'] = page
    if 'publicationId' not in element.attrib or element.attrib['publicationId'] != publication_id:
        print_styled("\tUpdated publication ID")
        element.attrib['publicationId'] = publication_id


def get_tag(element):
    tag = element.tag
    if "}" in tag:
        return tag.split("}")[1]
    return tag


def get_or_create_sub_element(element, tag, attrib: dict[str:str] = None, assign_id=False):
    attrib_path_str = "{*}" + tag  # Any namespace
    if attrib:
        for key, value in attrib.items():
            attrib_path_str += f"[@{key}='{value}']"
    sub_element = element.find(attrib_path_str)
    if sub_element is not None:
        return sub_element
    if assign_id:
        attrib.update({'id': get_random_bs_id()})
    if attrib:
        return ET.SubElement(element, tag, attrib)
    return ET.SubElement(element, tag)
