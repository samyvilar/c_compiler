__author__ = 'samyvilar'

from front_end import List

from front_end.parser.symbol_table import SymbolTable
from front_end.parser.declarations.declarations import translation_unit


class Parse(List):
    def __init__(self, tokens=(), symbol_table=None):
        symbol_table = symbol_table or SymbolTable()
        super(Parse, self).__init__(translation_unit(tokens, symbol_table))