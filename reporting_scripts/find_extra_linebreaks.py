from system.constants import SystemSettingsKeys, GameImportSpecs
from system.system import System

if __name__ == '__main__':
    system = System('horus-heresy',
                    settings={
                        SystemSettingsKeys.GAME_IMPORT_SPEC: GameImportSpecs.HERESY,
                    },
                    )
    # get a list of all LA
    legion_ids = []
    legion_root = system.all_nodes.get(lambda x: x.id == "4a48-4935-246d-0c2e")
    all_nodes_with_linebreaks = system.all_nodes.filter(
        lambda x: x.text and x.text.strip() and "\n" in x.text.strip())
    for node in all_nodes_with_linebreaks:
        node_text = node.text.strip()
        suspicious = False

        for line in node_text.splitlines():
            line = line.strip()
            if not line:
                continue
            first_char_in_line = line[0]
            if first_char_in_line != first_char_in_line.upper():
                suspicious = True
        if suspicious:
            print("\n=============")
            print(node)
            print(node.text.strip())
