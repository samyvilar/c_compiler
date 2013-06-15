__author__ = 'samyvilar'

from front_end import List

from front_end.parser.symbol_table import SymbolTable

from back_end.emitter.object_file import Symbol
from back_end.emitter.declarations.declaration import get_directives


class Emit(List):
    def __init__(self, ext_decs=(), symbol_table=None, directives=get_directives()):
        symbols, symbol_table = [], symbol_table or SymbolTable()
        if ext_decs and isinstance(ext_decs[0], Symbol):
            symbols = ext_decs
        else:
            for dec in ext_decs:
                symbol = directives[type(dec)](dec, symbol_table)
                _ = symbol and symbols.append(symbol)
        super(Emit, self).__init__(symbols)