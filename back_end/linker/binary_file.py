__author__ = 'samyvilar'


class BinaryFile(object):
    def __init__(self, symbol_table, bins, entry_point):
        self.symbol_table, self.bins, self.entry_point = symbol_table, bins, entry_point
