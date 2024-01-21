import collections
from typing import Callable

from system.node import Node


class NodeCollection(collections.UserList):
    def __init__(self, nodes: list[Node]):
        super().__init__(nodes)

    def filter(self, sort_condition: Callable[[Node], bool]):
        return NodeCollection([node for node in self._inner_list if sort_condition(node)])
