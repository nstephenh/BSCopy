import os
import unittest
from xml.etree import ElementTree as ET
from system.system import System
from system.system_file import get_tag
from settings import default_data_directory

def compare_elements(el1, el2):
    if get_tag(el1) != get_tag(el2):
        return False, f"Tag mismatch: {get_tag(el1)} != {get_tag(el2)}"
    
    # Compare attributes (ignoring order and namespace)
    # We ignore 'comment' as it might be present in JSON but not XML if XML was cleaned
    ignored_attrs = ['xmlns', 'comment']
    attr1 = {k: v.lower() if v in ['true', 'false', 'True', 'False'] else v for k, v in el1.attrib.items() 
             if not k.startswith('xmlns') and k not in ignored_attrs}
    attr2 = {k: v.lower() if v in ['true', 'false', 'True', 'False'] else v for k, v in el2.attrib.items() 
             if not k.startswith('xmlns') and k not in ignored_attrs}
    
    if attr1 != attr2:
        return False, f"Attribute mismatch in {get_tag(el1)}: {attr1} != {attr2}"
    
    # Compare text
    t1 = el1.text.strip() if el1.text else ""
    t2 = el2.text.strip() if el2.text else ""
    if t1 != t2:
        return False, f"Text mismatch in {get_tag(el1)}: '{t1}' != '{t2}'"
    
    # Compare children (ignoring order of containers and ignoring 'comment' elements)
    el1_children = [c for c in el1 if get_tag(c) != 'comment']
    el2_children = [c for c in el2 if get_tag(c) != 'comment']
    
    if len(el1_children) != len(el2_children):
        c1_tags = [get_tag(c) for c in el1_children]
        c2_tags = [get_tag(c) for c in el2_children]
        return False, f"Children count mismatch in {get_tag(el1)}: {len(el1_children)} != {len(el2_children)}. Tags 1: {c1_tags[:10]}, Tags 2: {c2_tags[:10]}"
    
    # For BS nodes, order might differ between XML and JSON if they are mixed
    # We'll try to match by tag and name/id if available
    for c1 in el1_children:
        match = None
        c1_tag = get_tag(c1)
        c1_name = c1.get('name')
        c1_id = c1.get('id')
        
        for i, c2 in enumerate(el2_children):
            if get_tag(c2) == c1_tag:
                if c1_id and c2.get('id') == c1_id:
                    match = el2_children.pop(i)
                    break
                elif c1_name and c2.get('name') == c1_name:
                    match = el2_children.pop(i)
                    break
        
        if match is None:
            # Try first available with same tag if no name/id
            for i, c2 in enumerate(el2_children):
                if get_tag(c2) == c1_tag:
                    match = el2_children.pop(i)
                    break
        
        if match is None:
            # DEBUG: Show what's in el2_children
            el2_tags = [get_tag(c) for c in el2_children]
            return False, f"Could not find match for child {c1_tag} (name={c1_name}, id={c1_id}) in {get_tag(el1)}. Available tags in target: {el2_tags}"
            
        equal, reason = compare_elements(c1, match)
        if not equal:
            return False, reason
            
    return True, ""

class TestJsonRegression(unittest.TestCase):
    def test_hh3_regression(self):
        xml_system_name = "hh3-original"
        json_system_name = "horus-heresy-3rd-edition"
        
        xml_path = os.path.join(default_data_directory, xml_system_name)
        json_path = os.path.join(default_data_directory, json_system_name)
        
        if not os.path.exists(xml_path):
            self.skipTest(f"XML system {xml_system_name} not found at {xml_path}")
        if not os.path.exists(json_path):
            self.skipTest(f"JSON system {json_system_name} not found at {json_path}")
            
        # Load XML system
        print(f"Loading XML system: {xml_system_name}")
        xml_system = System(xml_system_name, load_silent=True)
        
        # Load JSON system
        print(f"Loading JSON system: {json_system_name}")
        json_system = System(json_system_name, load_silent=True)
        
        # Compare
        print("Comparing trees...")
        for xml_file in xml_system.files:
            # Only compare .gst and .cat files
            if not (xml_file.name.endswith('.gst') or xml_file.name.endswith('.cat')):
                continue
            
            # Find corresponding file in json_system
            base_name = os.path.splitext(xml_file.name)[0]
            json_file = next((f for f in json_system.files if os.path.splitext(f.name)[0] == base_name), None)
            
            if json_file is None:
                print(f"Warning: Could not find corresponding JSON file for {xml_file.name}, skipping.")
                continue
            
            print(f"Comparing {xml_file.name} vs {json_file.name}")
            equal, reason = compare_elements(xml_file._source_tree.getroot(), json_file._source_tree.getroot())
            self.assertTrue(equal, f"Mismatch in {xml_file.name}: {reason}")
            
        print("Success! All matching files are identical.")

if __name__ == "__main__":
    unittest.main()
