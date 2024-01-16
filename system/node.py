from typing import TYPE_CHECKING
from xml.etree import ElementTree as ET

if TYPE_CHECKING:
    from system.system_file import SystemFile


class Node:

    def __init__(self, system_file: 'SystemFile', element: ET.Element):
        self.name = None

        self.system_file = system_file
        self.element = element
        self.id = element.attrib.get('id')
        if not self.id:
            raise Exception("Node initialization attempted on element with no ID")

        self.tag = element.tag.split('}')[1]
        if not self.is_link():
            self.name = element.attrib.get('name')

    def is_link(self):
        return self.element.attrib.get('targetId') is not None
