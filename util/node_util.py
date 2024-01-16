from util.log_util import print_styled


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
