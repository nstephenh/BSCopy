from system.constants import SystemSettingsKeys, GameImportSpecs
from system.system import System

if __name__ == '__main__':
    logfile = open('all_text.txt', 'w', encoding="utf-8")


    def log(file, text):
        print(text)
        try:
            file.write(text + "\n")
        except UnicodeEncodeError as e:
            file.write("Could not encode the text: " + str(e) + "\n")


    system = System('wh40k-10e',
                    settings={
                        SystemSettingsKeys.GAME_IMPORT_SPEC: GameImportSpecs.HERESY2E,
                    },
                    )
    # get a list of all LA
    legion_ids = []
    legion_root = system.all_nodes.get(lambda x: x.id == "4a48-4935-246d-0c2e")
    all_nodes_with_text = system.all_nodes.filter(
        lambda x: x.text and len(x.text.strip()) > 4 and x.tag not in ["comment"])

    for node in all_nodes_with_text:
        node_text = node.text.strip()
        log(logfile, "\n=============")
        log(logfile, str(node))
        log(logfile, node.text.strip())

