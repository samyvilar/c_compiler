__author__ = 'samyvilar'

from front_end.parser.ast.declarations import Static
from utils import get_attribute_func


class Symbol(object):
    def __init__(self, name, binaries, size, storage_class, location):
        self.binaries, self.storage_class, self.size = binaries, storage_class, size
        self.location = location  # Static definitions have the names mangled so as to isolate them to each file ...
        self.name = '{f}.{n}'.format(f=location.file_name, n=name) if isinstance(storage_class, Static) else name


class Data(Symbol):  # Global definition or declaration of a data type.
    pass


class Code(Symbol):  # Function Code.
    pass


class Reference(object):
    def __init__(self, symbol_name):
        self.name = symbol_name

binaries = get_attribute_func('binaries')
size = get_attribute_func('size')


def is_reference(obj):
    return isinstance(obj, Reference)
