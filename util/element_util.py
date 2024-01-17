from util.log_util import print_styled


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
