__author__ = 'samyvilar'

from itertools import ifilterfalse
from sequences import peek, consume

from front_end.parser.ast.declarations import TypeDef, EmptyDeclaration
from front_end.parser.symbol_table import SymbolTable

from back_end.emitter.declarations.declaration import get_directives


def _apply(declarations, symbol_table, directives):
    terminal = object()
    while peek(declarations, default=terminal) is not terminal:
        yield directives[type(peek(declarations))](consume(declarations), symbol_table)


def emit(declarations=(), symbol_table=None, directives=get_directives()):
    return _apply(
        ifilterfalse(lambda dec: isinstance(dec, (TypeDef, EmptyDeclaration)), declarations),
        symbol_table or SymbolTable(),
        directives
    )