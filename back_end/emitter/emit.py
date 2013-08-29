__author__ = 'samyvilar'

from itertools import ifilterfalse

from front_end.parser.ast.declarations import TypeDef, EmptyDeclaration
from front_end.parser.symbol_table import SymbolTable

from back_end.emitter.declarations.declaration import get_directives


def _apply(declarations, symbol_table, directives):
    return (directives[type(d)](d, symbol_table) for d in declarations)


def emit(declarations=(), symbol_table=None, directives=get_directives(), ignore=(TypeDef, EmptyDeclaration)):
    return _apply(
        ifilterfalse(lambda dec: isinstance(dec, ignore), declarations), symbol_table or SymbolTable(), directives
    )