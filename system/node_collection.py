from typing import Callable

from system.node import Node


class NodeCollection:
    def __init__(self):
        self.nodes: list[Node] = []

    def filter(self, sort_condition: Callable[[Node], bool]):
        new_collection = NodeCollection()
        new_collection.nodes = [node for node in self.nodes if sort_condition(node)]
        return new_collection
