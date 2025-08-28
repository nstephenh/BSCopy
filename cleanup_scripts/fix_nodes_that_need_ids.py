from system.system import System

from util.element_util import elements_that_get_id
from util.generate_util import get_random_bs_id

if __name__ == '__main__':
    system = System('horus-heresy')

    for node in system.all_nodes:
        if node.tag in elements_that_get_id and (node.id is None or node.id == ""):
            print(f"Setting ID for {node}")
            node.attrib.update({"id": get_random_bs_id()})

    system.save_system()
