def get_description(node):
    if not node:
        return ""
    for child in node:
        if child.tag.endswith('description'):
            return child
    return ""
