__author__ = 'samyvilar'

from logging_config import logging

from front_end.loader.locations import loc, LocationNotSet

from front_end.tokenizer.tokens import TOKENS
from front_end.parser.types import VoidType, CharType, ShortType, IntegerType, LongType, FloatType, DoubleType, CType
from front_end.parser.types import StructType

from front_end.parser.ast.declarations import Declaration, Definition
from front_end.parser.ast.statements import LabelStatement, GotoStatement, ReturnStatement

stack = []
logger = logging.getLogger('parser')


SymbolNotFoundError = KeyError


class SymbolTable(dict):
    def __init__(self, *args, **kwargs):
        self._stack = [{
            TOKENS.VOID: VoidType(LocationNotSet),
            TOKENS.CHAR: CharType(LocationNotSet),
            TOKENS.SHORT: ShortType(LocationNotSet),
            TOKENS.INT: IntegerType(LocationNotSet),
            TOKENS.LONG: LongType(LocationNotSet),
            TOKENS.FLOAT: FloatType(LocationNotSet),
            TOKENS.DOUBLE: DoubleType(LocationNotSet),
            TOKENS.STRUCT: StructType(None, None, LocationNotSet),
        }]
        self._stmnts = {'return': [], 'goto': [], 'label': {}}
        super(SymbolTable, self).__init__(*args, **kwargs)

    def __setitem__(self, key, value):
        # labels have different scoping rules then normal symbols.
        if isinstance(value, LabelStatement):
            if key in self.label_stmnts:
                raise ValueError('{l} Duplicate declaration of {label} previous at {at}'.format(
                    l=loc(value), label=key, at=loc(self.label_stmnts[key])
                ))
            self.label_stmnts[key] = value
        elif isinstance(value, GotoStatement):
            self.goto_stmnts.append(value)
        elif isinstance(value, ReturnStatement):
            self.return_stmnts.append(value)
        elif self.__contains__(key) and isinstance(self.__getitem__(key), Definition):
            raise ValueError('{l} Symbol {s} already in current scope previous definition at {at}'.format(
                l=loc(key), at=loc(self.__getitem__(key)), s=key
            ))
        elif self.__contains__(key) and isinstance(self.__getitem__(key), Declaration):
            if self.__getitem__(key) != value:
                raise ValueError('{l} Duplicate declaration of {v} mismatch, previous at {at}'.format(
                    l=loc(value), v=value, at=loc(self.__getitem__(key))
                ))
            logger.warning('{l} Redeclaring symbol {v} of same type ...'.format(l=loc(value), v=key))
        elif self.__contains__(key, search_all=True) and isinstance(value, (Declaration, CType)):
            logger.warning('{l} Symbol {s} shadowing previous instance at {at}.'.format(
                l=loc(key), s=key, at=loc(self.__getitem__(key))
            ))
        next(self.stack)[key] = value

    def __getitem__(self, item):  # search all frames.
        for table in self.stack:
            if item in table:
                return table[item]
        raise KeyError('{l} Could not locate symbol {item}'.format(item=item, l=loc(item)))

    def push_frame(self):  # Used for function definitions to keep track of labels, gotos, and return exps
        self._stmnts = {'return': [], 'goto': [], 'label': {}}
        self.push_name_space()

    @property
    def _stmnts(self):
        return self[' stmnts ']

    @_stmnts.setter
    def _stmnts(self, value):
        self[' stmnts '] = value

    @property
    def return_stmnts(self):
        return self._stmnts['return']

    @property
    def goto_stmnts(self):
        return self._stmnts['goto']

    @property
    def label_stmnts(self):
        return self._stmnts['label']

    def pop_frame(self):
        self.pop_name_space()

    def push_name_space(self):
        self._stack.append({})

    def pop_name_space(self):
        return self._stack.pop()

    def __contains__(self, item, search_all=False):  # only checks if its in the current frame.
        return any(item in frame for frame in self.stack) if search_all else item in next(self.stack)

    def pop(self, k, d=None):  # only pop within the current frame.
        if self.__contains__(k):
            return next(self.stack).pop(k, d)
        if d is not None:
            return d
        raise KeyError('{l} Could not locate symbol {item}'.format(item=k, l=loc(k)))

    def get(self, k, d=None):  # search all frames.
        try:
            return self.__getitem__(k)
        except KeyError as _:
            return d

    @property
    def stack(self):
        return reversed(self._stack)

    def __nonzero__(self):
        return bool(self.stack)