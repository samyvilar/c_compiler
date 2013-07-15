__author__ = 'samyvilar'

from logging_config import logging

from front_end.loader.locations import loc
from front_end.parser.ast.declarations import Declaration

logger = logging.getLogger('parser')


class SymbolTable(object):
    def __init__(self):
        self.stack = [{}]

    def __setitem__(self, key, value):
        if key in self:
            if isinstance(self[key], Declaration):
                if self[key] != value:
                    raise ValueError('{l} Duplicate declaration of {v} mismatch, previous at {at}'.format(
                        l=loc(value), v=value, at=loc(self[key])
                    ))
                logger.warning('{l} Redeclaring symbol {v} of same type ...'.format(l=loc(value), v=key))
            else:
                raise ValueError('{l} Symbol {s} already in current scope previous definition at {at}'.format(
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