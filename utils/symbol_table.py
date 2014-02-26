__author__ = 'samyvilar'

from itertools import imap, ifilter, chain

from front_end.loader.locations import loc
from front_end.parser.ast.declarations import Declaration, name
from front_end.parser.types import c_type

from utils.rules import identity


no_default = object()


def declaration(dec):
    return Declaration(dec.name, c_type(dec), loc(dec), dec.storage_class)


class SymbolTable(object):
    def __init__(self, args=(), **kwargs):
        self.stack = [dict(chain(getattr(args, 'iteritems', lambda a=args: a)(), kwargs.iteritems()))]

    def __setitem__(self, key, value):
        if key in self:
            raise ValueError('{l} Duplicate Symbol {s} previous at {at}'.format(l=loc(key), s=key, at=loc(self[key])))
        self.stack[-1][key] = value

    def update(self, args, **named_entries):
        func = identity
        if hasattr(args, 'iteritems'):
            func = lambda values: values.iteritems()
        for key, value in chain(func(args), named_entries.iteritems()):
            self[key] = value

    def __getitem__(self, item):  # search all frames.
        try:
            return next(ifilter(lambda table, i=item: i in table, reversed(self.stack)), {})[item]
        except KeyError as _:
            raise KeyError('{l} Could not locate symbol {item}'.format(item=item, l=loc(item)))

    def __contains__(self, item, search_all=False):  # only checks if its in the current frame.
        return any(item in frame for frame in reversed(self.stack)) if search_all else item in self.stack[-1]

    def get(self, k, default=None):  # search all frames.
        try:
            return self[k]
        except KeyError as _:
            return default

    def __nonzero__(self):
        return bool(self.stack)

    def setdefault(self, key, value):
        _ = self.stack[-1].setdefault(key, value)

    def pop(self, key):
        return self.stack[-1].pop(key)

    def itervalues(self):  # iterates over current frame ...
        return self.stack[-1].itervalues()


def push(symbol_table):
    symbol_table.stack.append({})
    return symbol_table


def pop(symbol_table):
    return symbol_table.stack.pop()


def get_symbols(symbol_table, *symbols):
    return imap(symbol_table.__getitem__, symbols)