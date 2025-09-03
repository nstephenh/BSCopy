from system.constants import SystemSettingsKeys, GameImportSpecs
from system.system import System

if __name__ == '__main__':
    system = System('horus-heresy-3rd-edition',
                    settings={
                        SystemSettingsKeys.GAME_IMPORT_SPEC: GameImportSpecs.HERESY3E,
                    },
                    )
    for prime_id in ["2c90-1d52-7075-59d3", "20cb-4eec-0844-8a97", "8cf8-9be5-91d6-c96d"]:
        for condition in system.all_nodes.filter(lambda x:
                                                 x.tag == "condition"
                                                 and x.attrib.get("childId") == prime_id
                                                 ):
            if condition.attrib["scope"] == "parent":
                condition.attrib["scope"] = "unit"

    system.save_system()
