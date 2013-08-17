__author__ = 'samyvilar'

from logging_config import logging

from front_end.loader.locations import loc
from front_end.parser.ast.declarations import Declaration
from front_end.parser.types import c_type

logger = logging.getLogger('parser')


def declaration(dec):
    return Declaration(dec.name, c_type(dec), loc(dec), dec.storage_class)


class SymbolTable(object):
    def __init__(self):
        self.stack = [{}]

    def __setitem__(self, key, value):
        # C allows multiple declarations, so long as long they are all consistent, with previous declarations
        # AND a single definition.
        # possible scenarios
        # 1) Giving a declaration, check its consistent with previous declaration or definition if any.
        # 2) Giving a definition, check its consistent with previous declaration and its consistent with previous
        # declaration if any.

        if isinstance(value, Declaration) and key in self:  # either function definition, definition or declaration.
            if declaration(self[key]) == declaration(value):  # check for consistency.
                if type(self[key]) is Declaration:  # if previous is declaration pop it and insert new either def or dec
                    _ = self.pop(key)
            else:
                raise ValueError('{l} inconsistent def/dec with previous at {a}'.format(l=loc(value), a=loc(self[key])))

        if key in self:
            raise ValueError('{l} Duplicate Symbol {s} previous at {at}'.format(
                l=loc(key), s=key, at=loc(self[key])
            ))
        self.stack[-1][key] = value

    def __getitem__(self, item):  # search all frames.
        for table in reversed(self.stack):
            if item in table:
                return table[item]
        raise KeyError('{l} Could not locate symbol {item}'.format(item=item, l=loc(item)))

    def __contains__(self, item, search_all=False):  # only checks if its in the current frame.
        return any(item in frame for frame in reversed(self.stack)) if search_all else item in self.stack[-1]

    def get(self, k, *d):  # search all frames.
        try:
            return self[k]
        except KeyError as er:
            if d:
                return d[0]
            raise er

    def __nonzero__(self):
        return bool(self.stack)

    def setdefault(self, key, value):
        _ = self.stack[-1].setdefault(key, value)

    def pop(self, key):
        return self.stack[-1].pop(key)

    def itervalues(self):
        return self.stack[-1].itervalues()


def push(symbol_table):
    symbol_table.stack.append({})
    return symbol_table


def pop(symbol_table):
    return symbol_table.stack.pop()