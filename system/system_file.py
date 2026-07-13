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
            
            if key == "alias" and clean_tag == 'categoryEntry':
                # GST often has category aliases as a child element or attribute?
                # The fail said: Text mismatch in rule: '' != '['Command']'
                # Wait, it was clean_tag == 'rule' that failed? No, 'alias' under 'categoryEntry'?
                # The traceback said: Text mismatch in rule: '' != '['Command']'
                # But my previous run had: Text mismatch in alias: 'Command' != ''
                if isinstance(value, list):
                    for item in value:
                        element.append(_dict_to_element_recursive('alias', item))
                else:
                    element.append(_dict_to_element_recursive('alias', value))
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
            if key == 'forceEntries' or key == 'forceEntry':
                plural_container_tag = 'forceEntries'
                singular_tag = 'forceEntry'
            elif key == 'costTypes' or key == 'costType':
                plural_container_tag = 'costTypes'
                singular_tag = 'costType'
            elif key == 'selectionEntries':
                plural_container_tag = 'selectionEntries'
                singular_tag = 'selectionEntry'
            elif key == 'selectionEntry':
                if clean_tag == 'catalogue': plural_container_tag = 'sharedSelectionEntries'
                else: plural_container_tag = 'selectionEntries'
                singular_tag = 'selectionEntry'
            elif key == 'selectionEntryGroups':
                plural_container_tag = 'selectionEntryGroups'
                singular_tag = 'selectionEntryGroup'
            elif key == 'selectionEntryGroup':
                if clean_tag == 'catalogue': plural_container_tag = 'sharedSelectionEntryGroups'
                else: plural_container_tag = 'selectionEntryGroups'
                singular_tag = 'selectionEntryGroup'
            elif key == 'rules':
                plural_container_tag = 'rules'
                singular_tag = 'rule'
            elif key == 'rule':
                if clean_tag == 'catalogue': plural_container_tag = 'sharedRules'
                else: plural_container_tag = 'rules'
                singular_tag = 'rule'
            elif key == 'profiles':
                plural_container_tag = 'profiles'
                singular_tag = 'profile'
            elif key == 'profile':
                if clean_tag == 'catalogue': plural_container_tag = 'sharedProfiles'
                else: plural_container_tag = 'profiles'
                singular_tag = 'profile'
            elif key == 'infoLinks' or key == 'infoLink': plural_container_tag = 'infoLinks'; singular_tag = 'infoLink'
            elif key == 'catalogueLinks' or key == 'catalogueLink': plural_container_tag = 'catalogueLinks'; singular_tag = 'catalogueLink'
            elif key == 'entryLinks' or key == 'entryLink': plural_container_tag = 'entryLinks'; singular_tag = 'entryLink'
            elif key == 'sharedSelectionEntries' or key == 'sharedSelectionEntry': 
                plural_container_tag = 'sharedSelectionEntries'
                singular_tag = 'selectionEntry'
            elif key == 'sharedSelectionEntryGroups' or key == 'sharedSelectionEntryGroup':
                plural_container_tag = 'sharedSelectionEntryGroups'
                singular_tag = 'selectionEntryGroup'
            elif key == 'sharedInfoLinks' or key == 'sharedInfoLink':
                plural_container_tag = 'sharedInfoLinks'
                singular_tag = 'infoLink'
            elif key == 'sharedProfiles' or key == 'sharedProfile':
                plural_container_tag = 'sharedProfiles'
                singular_tag = 'profile'
            elif key == 'sharedRules' or key == 'sharedRule':
                plural_container_tag = 'sharedRules'
                singular_tag = 'rule'
            elif key == 'costs' or key == 'cost': plural_container_tag = 'costs'; singular_tag = 'cost'
            elif key == 'constraints' or key == 'constraint': plural_container_tag = 'constraints'; singular_tag = 'constraint'
            elif key == 'modifiers' or key == 'modifier': plural_container_tag = 'modifiers'; singular_tag = 'modifier'
            elif key == 'modifierGroups' or key == 'modifierGroup': plural_container_tag = 'modifierGroups'; singular_tag = 'modifierGroup'
            elif key == 'characteristics' or key == 'characteristic': plural_container_tag = 'characteristics'; singular_tag = 'characteristic'
            elif key == 'conditions' or key == 'condition': plural_container_tag = 'conditions'; singular_tag = 'condition'
            elif key == 'conditionGroups' or key == 'conditionGroup': plural_container_tag = 'conditionGroups'; singular_tag = 'conditionGroup'
            elif key == 'repeats' or key == 'repeat': plural_container_tag = 'repeats'; singular_tag = 'repeat'
            elif key == 'categoryLinks' or key == 'categoryLink': plural_container_tag = 'categoryLinks'; singular_tag = 'categoryLink'
            elif key == 'categoryEntries' or key == 'categoryEntry': plural_container_tag = 'categoryEntries'; singular_tag = 'categoryEntry'
            elif key == 'publications' or key == 'publication': plural_container_tag = 'publications'; singular_tag = 'publication'

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
    for key, value in element.attrib.items():
        res[key] = value
    if element.text and element.text.strip():
        res["_text"] = element.text.strip()

    parent_tag = get_tag(element)
    for child in element:
        tag = get_tag(child)
        child_res = _element_to_dict_recursive(child)

        # Check if we should collapse this child into a list on the parent
        is_plural_container = False
        if parent_tag.endswith('s'):
            if parent_tag.endswith('ies') and tag.endswith('y'):
                is_plural_container = True
            elif parent_tag.endswith('Entries') and tag == parent_tag[:-7] + 'Entry':
                is_plural_container = True
            elif parent_tag.endswith('Groups') and tag == parent_tag[:-6] + 'Group':
                is_plural_container = True
            elif parent_tag.endswith('Links') and tag == parent_tag[:-5] + 'Link':
                is_plural_container = True
            elif parent_tag == 'costs' and tag == 'cost':
                is_plural_container = True
            elif parent_tag == 'rules' and tag == 'rule':
                is_plural_container = True
            elif parent_tag == 'profiles' and tag == 'profile':
                is_plural_container = True
            elif parent_tag == 'constraints' and tag == 'constraint':
                is_plural_container = True
            elif parent_tag == 'modifiers' and tag == 'modifier':
                is_plural_container = True

        if is_plural_container:
            # We use a special key '_items' or just put them in a list?
            # If we put them in a list directly under the parent's tag in the grandparent, 
            # that doesn't work because the parent exists.
            # We should put them in a list under a special key or just use the tag.
            # The current implementation uses the tag.
            pass

        if tag in res:
            if not isinstance(res[tag], list):
                res[tag] = [res[tag]]
            res[tag].append(child_res)
        else:
            res[tag] = child_res
    return res


def get_tag(element: ET.Element) -> str:
    tag = element.tag
    if "}" in tag:
        return tag.split("}")[1]
    return tag
