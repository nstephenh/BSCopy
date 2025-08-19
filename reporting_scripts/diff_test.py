# Force python XML parser not faster C accelerators
# because we can't hook the C implementation
import sys

sys.modules['_elementtree'] = None

from system.constants import SystemSettingsKeys, GameImportSpecs
from system.system import System

if __name__ == '__main__':
    system = System('horus-heresy-3rd-edition',
                    settings={
                        SystemSettingsKeys.GAME_IMPORT_SPEC: GameImportSpecs.HERESY3E,
                        "diff": True
                    },
                    )
    crusade = system.get_node_by_id("8562-592c-8d4b-a1f0")

    print(crusade.start_line_number)
