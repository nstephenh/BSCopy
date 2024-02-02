from xml.etree import ElementTree as ET

from system.system import System
from settings import default_system, default_data_directory

# Scripts use these as the current active system, but attempting to move to a class-based implementation

system = System(default_system, default_data_directory)
files_in_system: dict[str, ET.ElementTree] = {sf.path: sf._source_tree for sf in system.files}

rules_list: dict[str, str] = {}
wargear_list: dict[str, str] = {}
category_list: dict[str, str] = {}
