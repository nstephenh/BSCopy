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

def reproduce(filename="Alpha Legion.json"):
    json_path = os.path.expanduser(f"~/BattleScribe/data/horus-heresy-3rd-edition/{filename}")
    if not os.path.exists(json_path):
        print(f"File not found: {json_path}")
        return
    
    print(f"\nChecking {filename}...")
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
    orig_cat = original_data['catalogue']
    new_cat = new_data['catalogue']
    
    # Compare the top-level keys order of the catalogue
    orig_cat_keys = list(orig_cat.keys())
    new_cat_keys = list(new_cat.keys())
    
    print(f"Original catalogue keys: {orig_cat_keys}")
    print(f"New catalogue keys:      {new_cat_keys}")

    if orig_cat_keys != new_cat_keys:
        print(f"Catalogue keys differ in order or presence!")
        # Find which ones are different
        for i in range(max(len(orig_cat_keys), len(new_cat_keys))):
            o = orig_cat_keys[i] if i < len(orig_cat_keys) else "MISSING"
            n = new_cat_keys[i] if i < len(new_cat_keys) else "MISSING"
            if o != n:
                 print(f"  {i}: {o} vs {n}")
    else:
        print("Catalogue keys match in order.")

    # Specific check for sharedSelectionEntries being first
    # (Removed enforce check as per new requirement to remove priority lists)
    print(f"First key in catalogue: {new_cat_keys[0]}")

    orig_entries = orig_cat['sharedSelectionEntries']
    new_entries = new_cat['sharedSelectionEntries']
    
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

    # Check order of keys in the first entry of sharedSelectionEntries
    if orig_entries and new_entries:
        o_keys = list(orig_entries[0].keys())
        n_keys = list(new_entries[0].keys())
        print(f"Original keys in first entry: {o_keys}")
        print(f"New keys in first entry:      {n_keys}")
        if o_keys != n_keys:
            print("Keys in first entry differ in order!")
        else:
            print("Keys in first entry match in order.")
    
    # Save a temporary copy to see the difference
    with open("repro_output.json", 'w', encoding='utf-8') as f:
        json.dump(new_data, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    reproduce("Alpha Legion.json")
    reproduce("Legiones Astartes.json")
    reproduce("Weapons.json")
