import sys
import xml.etree.ElementTree as ET


# https://stackoverflow.com/questions/6949395/is-there-a-way-to-get-a-line-number-from-an-elementtree-element

class LineNumberingParser(ET.XMLParser):

    def __init__(self):
        super(self.__class__, self).__init__()
        # Force python XML parser not faster C accelerators
        # because we can't hook the C implementation
        if sys.modules['_elementtree'] is not None:
            raise Exception("Cannot use LineNumberingParser when using C accelerators,"
                            " ensure you have `sys.modules['_elementtree'] = None` before importing ET")

    def _start(self, *args, **kwargs):
        # Here we assume the default XML parser which is expat
        # and copy its element position attributes into output Elements
        element = super(self.__class__, self)._start(*args, **kwargs)
        element._start_line_number = self.parser.CurrentLineNumber
        element._start_column_number = self.parser.CurrentColumnNumber
        element._start_byte_index = self.parser.CurrentByteIndex
        return element

    def _end(self, *args, **kwargs):
        element = super(self.__class__, self)._end(*args, **kwargs)
        element._end_line_number = self.parser.CurrentLineNumber
        element._end_column_number = self.parser.CurrentColumnNumber
        element._end_byte_index = self.parser.CurrentByteIndex
        return element
