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
    if word.endswith('s'):
        return word, word[:-1]
    return word + 's', word


# Singular forms of elements that are nested inside a pluralized "container" element,
# e.g. <rules><rule/></rules>.
_PLURAL_CONTAINER_SINGULARS = {
    'forceEntry', 'costType', 'selectionEntry', 'selectionEntryGroup', 'rule', 'profile',
    'infoLink', 'forceEntryLink', 'catalogueLink', 'entryLink', 'cost', 'constraint',
    'modifier', 'modifierGroup', 'characteristic', 'condition', 'conditionGroup', 'repeat',
    'categoryLink', 'categoryEntry', 'publication', 'profileType', 'characteristicType'
}

# Singular forms which, when found directly under a catalogue, are wrapped in a "shared"
# container (e.g. sharedRules) instead of their regular plural container (e.g. rules).
_CATALOGUE_SHARED_SINGULARS = {'selectionEntry', 'selectionEntryGroup', 'rule', 'profile'}


def _dict_to_element_recursive(tag: str, data: dict or list or str) -> ET.Element:
    # Use simple tag for comparison
    clean_tag = tag.split('}')[-1] if '}' in tag else tag
    element = ET.Element(tag)
    if isinstance(data, dict):
        # We need to collect singular items that belong in plural containers
        wrapped_items = {} # plural_tag -> [ (singular_tag, item_data), ... ]
        
        # Attributes should be processed after children to avoid name collisions in some cases,
        # but here we use types to differentiate.
        
        for key, value in data.items():
            if key == "_text" or key == "$text":
                element.text = str(value)
                continue
            
            if key == "alias":
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
                    raise (ValueError("Expected list, dict or str for alias, got: {}, of type {}".format(value, type(value))))
                continue

            if key == "comment":
                # JSON has it as an attribute, but XML had it as a child.
                pass 

            if key == 'description' and clean_tag == 'rule':
                # Rule description is a child in BS XML, but an attribute in JSON.
                element.append(_dict_to_element_recursive('description', value))
                continue
            
            if not isinstance(value, (dict, list)):
                # Attribute
                if key != 'xmlns' and not key.startswith('xmlns:'):
                    element.set(key, str(value))
                continue
            
            # Key is a child element or list of children
            plural_container_tag = None
            singular_tag = key

            # 1. Determine if this key belongs in a plural container
            is_shared_key = key.startswith('shared') and len(key) > 6 and key[6].isupper()
            base_key = key[6].lower() + key[7:] if is_shared_key else key
            plural_form, singular_form = get_plural_and_singular(base_key)

            if singular_form in _PLURAL_CONTAINER_SINGULARS:
                singular_tag = singular_form
                if is_shared_key or (clean_tag == 'catalogue' and key == singular_form
                                      and singular_form in _CATALOGUE_SHARED_SINGULARS):
                    plural_container_tag = 'shared' + plural_form[0].upper() + plural_form[1:]
                else:
                    plural_container_tag = plural_form

            if plural_container_tag:
                if plural_container_tag not in wrapped_items:
                    wrapped_items[plural_container_tag] = []
                
                if isinstance(value, list):
                    for item in value:
                        wrapped_items[plural_container_tag].append((singular_tag, item))
                else:
                    wrapped_items[plural_container_tag].append((singular_tag, value))
            else:
                # Key is not a singular item needing wrapping
                element.append(_dict_to_element_recursive(key, value))

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
        element.text = str(data)
                
    return element


def element_to_dict(element: ET.Element) -> dict:
    """
    Convert an ElementTree Element to a dictionary.
    """
    return {get_tag(element): _element_to_dict_recursive(element)}


def _element_to_dict_recursive(element: ET.Element) -> dict or str:
    res = {}



    # 1. Children
    clean_parent_tag = get_tag(element)
    for child in element:
        tag = get_tag(child)
        child_res = _element_to_dict_recursive(child)

        # Check if we should collapse this child into a list on the parent
        is_plural_container = False
        plural_form, singular_form = get_plural_and_singular(tag)
        if singular_form in _PLURAL_CONTAINER_SINGULARS:
            # Check if this tag is indeed a plural container (e.g. "rules" containing "rule")
            all_children_are_singular = True
            for grand_child in child:
                if get_tag(grand_child) != singular_form:
                    all_children_are_singular = False
                    break
            if all_children_are_singular:
                is_plural_container = True
            
        # Forces common plural containers to be treated as such even if empty or containing other things (though they shouldn't)
        if tag in ['sharedSelectionEntries', 'sharedSelectionEntryGroups', 'sharedInfoLinks', 'sharedProfiles', 'sharedRules',
                    'selectionEntries', 'selectionEntryGroups', 'infoLinks', 'rules', 'profiles', 'costs', 'constraints',
                    'modifiers', 'modifierGroups', 'characteristics', 'conditions', 'conditionGroups', 'repeats',
                    'categoryEntries', 'categoryLinks', 'catalogueLinks', 'entryLinks', 'forceEntryLinks']:
            is_plural_container = True

        if is_plural_container:
            # Key is plural_form (e.g. "rules"), we want to store it as singular items (e.g. "rule": [...])
            key_in_dict = tag # default
            is_shared_key = tag.startswith('shared') and len(tag) > 6 and tag[6].isupper()
            if is_shared_key:
                # sharedRules -> sharedRule
                base_plural = tag[6].lower() + tag[7:] # "Rules" -> "rules"
                _, base_singular = get_plural_and_singular(base_plural)
                key_in_dict = 'shared' + base_singular[0].upper() + base_singular[1:]
            elif tag == 'sharedSelectionEntries':
                key_in_dict = 'selectionEntry'
            elif tag == 'sharedSelectionEntryGroups':
                key_in_dict = 'selectionEntryGroup'
            elif tag == 'sharedInfoLinks':
                key_in_dict = 'infoLink'
            elif tag == 'sharedProfiles':
                key_in_dict = 'profile'
            elif tag == 'sharedRules':
                key_in_dict = 'rule'
            elif tag == 'categoryEntries' and clean_parent_tag != 'catalogue':
                # categoryEntries -> categoryEntry
                key_in_dict = 'categoryEntry'
            elif tag == 'categoryLinks':
                key_in_dict = 'categoryLink'
            elif tag == 'forceEntryLinks':
                key_in_dict = 'forceEntryLink'
            elif tag == 'catalogueLinks':
                key_in_dict = 'catalogueLink'
            elif tag == 'entryLinks':
                key_in_dict = 'entryLink'
            elif tag == 'selectionEntries':
                key_in_dict = 'selectionEntry'
            elif tag == 'selectionEntryGroups':
                key_in_dict = 'selectionEntryGroup'
            elif tag == 'infoLinks':
                key_in_dict = 'infoLink'
            elif tag == 'costs':
                key_in_dict = 'cost'
            elif tag == 'rules':
                key_in_dict = 'rule'
            elif tag == 'profiles':
                key_in_dict = 'profile'
            elif tag == 'constraints':
                key_in_dict = 'constraint'
            elif tag == 'modifiers':
                key_in_dict = 'modifier'
            elif tag == 'modifierGroups':
                key_in_dict = 'modifierGroup'
            elif tag == 'characteristics':
                key_in_dict = 'characteristic'
            elif tag == 'conditions':
                key_in_dict = 'condition'
            elif tag == 'conditionGroups':
                key_in_dict = 'conditionGroup'
            elif tag == 'repeats':
                key_in_dict = 'repeat'
            else:
                key_in_dict = singular_form
            
            # Special case for shared containers in catalogue: preserve the container tag as key
            if clean_parent_tag == 'catalogue' and tag.startswith('shared'):
                # But wait, sharedSelectionEntries -> selectionEntry in some JSONs?
                # Let's check the original Alpha Legion.json again.
                # Actually, Alpha Legion.json HAS sharedSelectionEntries as a key.
                key_in_dict = tag

            # Extract the children as a list
            items = []
            for grand_child in child:
                items.append(_element_to_dict_recursive(grand_child))
            
            if not items:
                # If there are no items, we still want the key in the dict to represent an empty list
                if key_in_dict not in res:
                    res[key_in_dict] = []
                continue

            if key_in_dict in res:
                if not isinstance(res[key_in_dict], list):
                    res[key_in_dict] = [res[key_in_dict]]
                res[key_in_dict].extend(items)
            else:
                res[key_in_dict] = items
            continue

        if tag in res:
            if not isinstance(res[tag], list):
                res[tag] = [res[tag]]
            res[tag].append(child_res)
        else:
            res[tag] = child_res

    # 2. Text
    if element.text and element.text.strip():
        res["$text"] = element.text.strip()

    # 3. Attributes
    for key, value in element.attrib.items():
        res[key] = value


    return res


def get_tag(element: ET.Element) -> str:
    tag = element.tag
    if "}" in tag:
        return tag.split("}")[1]
    return tag
