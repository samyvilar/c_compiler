__author__ = 'samyvilar'

from logging_config import logging

from front_end.loader.locations import loc, LocationNotSet

from front_end.tokenizer.tokens import TOKENS
from front_end.parser.types import VoidType, CharType, ShortType, IntegerType, LongType, FloatType, DoubleType, CType
from front_end.parser.types import StructType

from front_end.parser.ast.declarations import Declaration, Definition

logger = logging.getLogger('parser')


class SymbolTable(object):
    def __init__(self):
        self.stack = [{
            TOKENS.VOID: VoidType(LocationNotSet),
            TOKENS.CHAR: CharType(LocationNotSet),
            TOKENS.SHORT: ShortType(LocationNotSet),
            TOKENS.INT: IntegerType(LocationNotSet),
            TOKENS.LONG: LongType(LocationNotSet),
            TOKENS.FLOAT: FloatType(LocationNotSet),
            TOKENS.DOUBLE: DoubleType(LocationNotSet),

            TOKENS.STRUCT: StructType(None, None, LocationNotSet),
            TOKENS.SIGNED: IntegerType(LocationNotSet),
            TOKENS.UNSIGNED: IntegerType(LocationNotSet),
        }]

    def __setitem__(self, key, value):
        if key in self and isinstance(self[key], (Definition, CType)):
            raise ValueError('{l} Symbol {s} already in current scope previous definition at {at}'.format(
                l=loc(key), s=key, at=loc(self[key])
            ))
        elif key in self and isinstance(self[key], Declaration):
            if self[key] != value:
                raise ValueError('{l} Duplicate declaration of {v} mismatch, previous at {at}'.format(
                    l=loc(value), v=value, at=loc(self[key])
                ))
            logger.warning('{l} Redeclaring symbol {v} of same type ...'.format(l=loc(value), v=key))
        elif self.__contains__(key, search_all=True) and isinstance(value, Declaration):
            logger.warning('{l} Symbol {s} shadows at {at}.'.format(l=loc(key), s=key, at=loc(self.__getitem__(key))))
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

    def itervalues(self):
        return self.stack[-1].itervalues()


def push(symbol_table):
    symbol_table.stack.append({})
    return symbol_table


def pop(symbol_table):
    return symbol_table.stack.pop()