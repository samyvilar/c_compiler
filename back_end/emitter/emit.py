__author__ = 'samyvilar'

from sequences import peek, consume

from front_end.parser.symbol_table import SymbolTable

from back_end.emitter.declarations.declaration import get_directives


def emit(declarations, symbol_table=None, directives=get_directives()):
    symbol_table = symbol_table or SymbolTable()
    while peek(declarations, default=False):
        yield directives[type(peek(declarations))](consume(declarations), symbol_table)