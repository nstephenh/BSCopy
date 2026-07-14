import json
import os
from system.system_file import element_to_dict, dict_to_element, SystemFile
from xml.etree import ElementTree as ET

from system.node_collection import NodeCollection

class MockSystem:
    def __init__(self):
        self.settings = {}
        self.all_nodes = NodeCollection([])
        self.nodes_with_ids = NodeCollection([])

def reproduce():
    json_path = os.path.expanduser("~/BattleScribe/data/horus-heresy-3rd-edition/Alpha Legion.json")
    with open(json_path, 'r', encoding='utf-8') as f:
        original_data = json.load(f)
    
    # Simulate loading and saving
    mock_system = MockSystem()
    system_file = SystemFile(mock_system, json_path)
    
    # Get data after round-trip
    new_data = element_to_dict(system_file._source_tree.getroot())
    
    # Compare keys of the first few levels
    original_keys = list(original_data.keys())
    new_keys = list(new_data.keys())
    
    if original_keys != new_keys:
        print(f"Root keys differ!")
        print(f"Original: {original_keys}")
        print(f"New:      {new_keys}")
    else:
        print("Root keys match.")

    # Compare names or IDs if they exist to see if order changed
    orig_entries = original_data['catalogue']['sharedSelectionEntries']
    new_entries = new_data['catalogue']['sharedSelectionEntries'] 
    
    orig_names = [i.get('name', i.get('id', 'unknown')) for i in orig_entries if isinstance(i, dict)]
    new_names = [i.get('name', i.get('id', 'unknown')) for i in new_entries if isinstance(i, dict)]
    
    print(f"Original names count: {len(orig_names)}")
    print(f"New names count:      {len(new_names)}")
    print(f"First 5 original: {orig_names[:5]}")
    print(f"First 5 new:      {new_names[:5]}")
    
    if orig_names != new_names:
        print(f"Order changed for sharedSelectionEntries!")
        for i in range(min(len(orig_names), len(new_names), 20)):
            o = orig_names[i] if i < len(orig_names) else "MISSING"
            n = new_names[i] if i < len(new_names) else "MISSING"
            print(f"  {i}: {o} vs {n}")
        
        # Check if set of names is the same
        if set(orig_names) == set(new_names):
            print("Set of names matches, order just changed.")
        else:
            print("Set of names DOES NOT match!")
            print(f"Missing in new: {set(orig_names) - set(new_names)}")
            print(f"Extra in new:   {set(new_names) - set(orig_names)}")
    else:
        print("sharedSelectionEntries order matches.")
    
    # Save a temporary copy to see the difference
    with open("repro_output.json", 'w', encoding='utf-8') as f:
        json.dump(new_data, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    reproduce()
