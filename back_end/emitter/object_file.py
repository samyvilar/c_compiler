__author__ = 'samyvilar'


class Symbol(object):
    def __init__(self, name, binaries, size, storage_class, location):
        self.name, self.binaries = name, binaries
        self.storage_class, self.size = storage_class, size
        self.location = location


class Data(Symbol):  # Global definition or declaration of a data type.
    pass


class Code(Symbol):  # Function Code.
    pass


def binaries(symbol):
    return getattr(symbol, 'binaries')


def size(symbol):
    return getattr(symbol, 'size')

