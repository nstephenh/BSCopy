import json
import os
from typing import TYPE_CHECKING
from xml.etree import ElementTree as ET

from system.line_numbering_parser import LineNumberingParser
from system.node import Node
from system.node_collection import NodeCollection
from util.generate_util import cleanup_file_match_bs_whitespace
from util.text_utils import make_plural

if TYPE_CHECKING:
    from system.system import System


class SystemFile:

    def __init__(self, system: 'System', path):
        self.system = system  # Link to parent
        self.name = os.path.split(path)[1]
        self.path = path

        self.is_gst = os.path.splitext(path)[1] == ".gst"
        self.is_json = os.path.splitext(path)[1] == ".json"
        self.is_template = "Template" in self.name

        self.namespace = set_namespace_from_file(path)

        self.all_nodes = NodeCollection([])
        self.nodes_with_ids = NodeCollection([])

        if self.is_json:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self._source_tree = ET.ElementTree(dict_to_element(data))
        elif self.system.settings.get("diff"):
            self._source_tree = ET.parse(path, parser=LineNumberingParser())
        else:
            self._source_tree = ET.parse(path)

        self.library = self._source_tree.getroot().get('library') == "true"
        self.id = self._source_tree.getroot().get('id')
        self.import_ids = [c.get('targetId') for c in
                           self._source_tree.findall(f'.//{self.get_namespace_tag()}catalogueLink')]
        self.revision = self._source_tree.getroot().get('revision')
        self.game_system_revision = self._source_tree.getroot().get('gameSystemRevision')

        self._parent_map = {c: p for p in self._source_tree.iter() for c in p}
        self.root_node = Node(self, self._source_tree.getroot(), is_root_node=True)

    def save(self):
        if self.is_json:
            data = element_to_dict(self._source_tree.getroot())
            with open(self.path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return

        ET.indent(self._source_tree)
        # utf-8 to keep special characters un-escaped.
        self._source_tree.write(self.path, encoding="utf-8")
        cleanup_file_match_bs_whitespace(self.path)

    def __str__(self):
        return self.name

    def get_namespace_tag(self) -> str:
        return "{" + self.namespace + "}"

    def get_or_create_shared_node(self, tag: str, attrib: dict = None) -> 'Node':
        """
        Create a node under this file's sharedPlural({tag})
        :return: The created node
        """
        parent_tag = tag
        shared_element_root_tag = f"shared{parent_tag[0].upper()}{make_plural(parent_tag[1:])}"
        parent = self.root_node.get_or_create_child(shared_element_root_tag)
        return parent.get_or_create_child(tag, attrib)

    @property
    def faction(self):
        pretty_name = self.root_node.name
        if not self.system.game:
            return None
        if pretty_name in self.system.game.FACTIONS:
            return pretty_name
        if " - " in pretty_name:
            name_component = pretty_name.split(" - ")[1]
            name_component = name_component.strip()
            if name_component in self.system.game.FACTIONS:
                return name_component


def get_namespace_from_file(filename: str):
    extension = os.path.splitext(filename)[1]
    if extension == ".cat":
        return "http://www.battlescribe.net/schema/catalogueSchema"
    elif extension == ".gst" or extension == ".json":
        return "http://www.battlescribe.net/schema/gameSystemSchema"


def set_namespace_from_file(filename):
    namespace = get_namespace_from_file(filename)
    ET.register_namespace("", namespace)
    return namespace


def read_categories(source_tree):
    category_map = {}
    categories_element = source_tree.find("{http://www.battlescribe.net/schema/catalogueSchema}categoryEntries")
    if categories_element is None:
        categories_element = source_tree.find("{http://www.battlescribe.net/schema/gameSystemSchema}categoryEntries")
    if categories_element is None:
        categories_element = source_tree.find("categoryEntries")

    if not categories_element:
        return
    for category_element in categories_element:
        name = category_element.get('name')
        if name.endswith(":"):
            name = name[:-1]
        if name.lower().endswith(" sub-type"):
            name = name[:-len(" sub-type")]
            if name.lower().endswith(" unit"):
                name = name[:-len(" unit")]
        elif name.lower().endswith(" unit-type"):
            name = name[:-len(" unit-type")]
        id = category_element.get('id')
        category_map[name] = id
    return category_map

def dict_to_element(data: dict) -> ET.Element:
    """
    Convert a dictionary to an ElementTree Element.
    The dictionary should have exactly one top-level key for the root element.
    """
    if len(data) != 1:
        raise ValueError("Dict must have exactly one root key")
    tag = list(data.keys())[0]
    return _dict_to_element_recursive(tag, data[tag])


def get_plural_and_singular(word: str) -> (str, str):
    """
    Given a word in either its singular or plural form, return a tuple of
    (plural, singular) forms for that word, using simple English pluralization
    rules (trailing "y" -> "ies", otherwise append/strip a trailing "s").
    """
    if word.endswith('ies'):
        return word, word[:-3] + 'y'
    if word.endswith('y'):
        return word[:-1] + 'ies', word

    # Exceptions for BattleScribe
    if word == 'alias' or word == 'aliases':
        return 'aliases', 'alias'
    if word == 'description' or word == 'descriptions':
        return 'description', 'description'

    if word.endswith('s') and not word.endswith('ss'):
        return word, word[:-1]
    return word + 's', word


def try_convert(value: str):
    if value.lower() == 'true':
        return True
    if value.lower() == 'false':
        return False
    try:
        if value.startswith('+'):
            return value
        if value.startswith('0') and len(value) > 1 and value[1].isdigit():
            return value
        if '.' in value:
            return float(value)
        return int(value)
    except ValueError:
        return value


def to_string(value):
    if isinstance(value, bool):
        return str(value).lower()
    return str(value)


# No longer using hardcoded lists for plural containers


def _dict_to_element_recursive(tag: str, data: dict or list or str) -> ET.Element:
    # Use simple tag for comparison
    clean_tag = tag.split('}')[-1] if '}' in tag else tag
    element = ET.Element(tag)
    if isinstance(data, dict):
        # We need to collect singular items that belong in plural containers
        wrapped_items = {}  # plural_tag -> [ (singular_tag, item_data), ... ]

        for key, value in data.items():
            if key == "_text" or key == "$text":
                element.text = to_string(value)
                continue

            if key == "alias" or key == "aliases":
                if isinstance(value, list):
                    for item in value:
                        element.append(_dict_to_element_recursive('alias', item))
                elif isinstance(value, dict):
                    element.append(_dict_to_element_recursive('alias', value))
                elif isinstance(value, str):
                    alias_el = ET.Element('alias')
                    alias_el.text = value
                    element.append(alias_el)
                else:
                    alias_el = ET.Element('alias')
                    alias_el.text = to_string(value)
                    element.append(alias_el)
                continue

            if key == "comment":
                # JSON has it as an attribute, but XML had it as a child.
                pass

            if key == 'description':
                # Rule description is a child in BS XML, but an attribute in JSON.
                element.append(_dict_to_element_recursive('description', value))
                continue

            if not isinstance(value, (dict, list)):
                # Attribute
                if key != 'xmlns' and not key.startswith('xmlns:'):
                    element.set(key, to_string(value))
                continue

            # Key is a child element or list of children
            plural_container_tag = None
            singular_tag = key

            plural_form, singular_form = get_plural_and_singular(key)

            if isinstance(value, list):
                # If it's a list, it's definitely a plural container in XML
                plural_container_tag = plural_form
                # Determine the singular tag for children
                if key.startswith('shared') and len(key) > 6 and key[6].isupper():
                    # sharedSelectionEntries -> selectionEntry
                    singular_tag = singular_form[6].lower() + singular_form[7:]
                else:
                    singular_tag = singular_form

                if plural_container_tag not in wrapped_items:
                    wrapped_items[plural_container_tag] = []
                for item in value:
                    wrapped_items[plural_container_tag].append((singular_tag, item))
            else:
                # Singular child, but use the singular tag name
                singular_tag = singular_form
                if key.startswith('shared') and len(key) > 6 and key[6].isupper():
                    singular_tag = singular_form[6].lower() + singular_form[7:]
                element.append(_dict_to_element_recursive(singular_tag, value))

        # Add wrapped items into containers
        for plural_tag, items in wrapped_items.items():
            if not items:
                continue
            container = None
            for child in element:
                if get_tag(child) == plural_tag:
                    container = child
                    break
            if container is None:
                # We need to make sure the container tag is correct (with namespace if applicable)
                container_tag = plural_tag
                if '}' in tag:
                    container_tag = tag.split('}')[0] + '}' + plural_tag
                container = ET.Element(container_tag)
                element.append(container)
            
            for s_tag, item_data in items:
                # Singular tag also needs namespace if applicable
                singular_tag_with_ns = s_tag
                if '}' in tag:
                    namespace = tag.split('}')[0] + '}'
                    singular_tag_with_ns = namespace + s_tag
                container.append(_dict_to_element_recursive(singular_tag_with_ns, item_data))

    elif isinstance(data, list):
        # Determine child tag if list key was plural
        child_tag = tag
        if tag == 'categoryEntries': child_tag = 'categoryEntry'
        elif tag == 'selectionEntries': child_tag = 'selectionEntry'
        elif tag == 'selectionEntryGroups': child_tag = 'selectionEntryGroup'
        elif tag == 'infoLinks': child_tag = 'infoLink'
        elif tag == 'forceEntryLinks': child_tag = 'forceEntryLink'
        elif tag == 'catalogueLinks': child_tag = 'catalogueLink'
        elif tag == 'entryLinks': child_tag = 'entryLink'
        elif tag == 'sharedSelectionEntries': child_tag = 'selectionEntry'
        elif tag == 'sharedSelectionEntryGroups': child_tag = 'selectionEntryGroup'
        elif tag == 'sharedInfoLinks': child_tag = 'infoLink'
        elif tag == 'sharedProfiles': child_tag = 'profile'
        elif tag == 'sharedRules': child_tag = 'rule'
        elif tag == 'costs': child_tag = 'cost'
        elif tag == 'rules': child_tag = 'rule'
        elif tag == 'profiles': child_tag = 'profile'
        elif tag == 'constraints': child_tag = 'constraint'
        elif tag == 'modifiers': child_tag = 'modifier'
        elif tag == 'modifierGroups': child_tag = 'modifierGroup'
        elif tag == 'characteristics': child_tag = 'characteristic'
        elif tag == 'conditions': child_tag = 'condition'
        elif tag == 'conditionGroups': child_tag = 'conditionGroup'
        elif tag == 'repeats': child_tag = 'repeat'
        elif tag == 'categoryLinks': child_tag = 'categoryLink'
        
        for item in data:
            element.append(_dict_to_element_recursive(child_tag, item))
    else:
        element.text = to_string(data)

    return element


def element_to_dict(element: ET.Element) -> dict:
    """
    Convert an ElementTree Element to a dictionary.
    """
    return {get_tag(element): _element_to_dict_recursive(element)}


def _element_to_dict_recursive(element: ET.Element) -> dict or str:
    res = {}

    # 1. Children
    for child in element:
        tag = get_tag(child)
        child_res = _element_to_dict_recursive(child)

        # Check if we should collapse this child into a list on the parent
        is_plural_container = False
        plural_form, singular_form = get_plural_and_singular(tag)

        if tag == plural_form and plural_form != singular_form:
            # It's a plural form tag, check if it's a container
            if not len(child):
                is_plural_container = True  # Empty container
            else:
                all_children_match = True
                for grand_child in child:
                    g_tag = get_tag(grand_child)
                    # Container 'sharedSelectionEntries' contains 'selectionEntry'
                    if tag.startswith('shared') and len(tag) > 6 and tag[6].isupper():
                        expected_singular = singular_form[6].lower() + singular_form[7:]
                    else:
                        expected_singular = singular_form

                    if g_tag != expected_singular:
                        all_children_match = False
                        break
                if all_children_match:
                    is_plural_container = True

        if is_plural_container:
            key_in_dict = tag  # Keep the plural tag as key

            # Extract the children as a list
            items = []
            for grand_child in child:
                items.append(_element_to_dict_recursive(grand_child))

            if key_in_dict in res:
                if not isinstance(res[key_in_dict], list):
                    res[key_in_dict] = [res[key_in_dict]]
                res[key_in_dict].extend(items)
            else:
                res[key_in_dict] = items
            continue

        # Regular child, pluralize the key
        p_tag, _ = get_plural_and_singular(tag)
        if p_tag in res:
            if not isinstance(res[p_tag], list):
                res[p_tag] = [res[p_tag]]
            res[p_tag].append(child_res)
        else:
            res[p_tag] = child_res

    # 2. Text
    if element.text and element.text.strip():
        res["$text"] = element.text.strip()

    # 3. Attributes
    for key, value in element.attrib.items():
        res[key] = try_convert(value)

    if len(res) == 1 and "$text" in res:
        return res["$text"]

    return res


def get_tag(element: ET.Element) -> str:
    tag = element.tag
    if "}" in tag:
        return tag.split("}")[1]
    return tag
