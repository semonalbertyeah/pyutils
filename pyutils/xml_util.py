# -*- coding:utf-8 -*-

import xml.parsers.expat

def valid_xml(path):
    parser = xml.parsers.expat.ParserCreate()
    try:
        parser.ParseFile(open(path, "r"))
        return True
    except xml.parsers.expat.ExpatError as e:
        return False




