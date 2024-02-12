import collections
from typing import Callable

from system.node import Node


class NodeCollection(collections.UserList):
    def __init__(self, nodes: list[Node]):
        super().__init__(nodes)

    def __str__(self) -> str:
        return str(self.data)

    def filter(self, sort_condition: Callable[[Node], bool]) -> 'NodeCollection':
        return NodeCollection(filter(sort_condition, self.data))

    def get(self, sort_condition: Callable[[Node], bool]) -> 'Node' or None:
        return next(filter(sort_condition, self.data), None)
