__author__ = 'samyvilar'

from itertools import ifilterfalse

from front_end.parser.ast.declarations import TypeDef, EmptyDeclaration
from front_end.parser.ast.statements import EmptyStatement
from front_end.parser.ast.expressions import EmptyExpression
from front_end.parser import SymbolTable

from back_end.emitter.declarations.declaration import get_directives
from back_end.emitter.statements.statement import statement as _statement_func
from back_end.emitter.expressions.expression import expression as _expression_func


def _apply(declarations, symbol_table, directives):
    return (directives[type(dec)](dec, symbol_table) for dec in declarations)


def emit(
    declarations=(),
    symbol_table=None,
    directives=get_directives(),
    ignore=(TypeDef, EmptyDeclaration, EmptyStatement, EmptyExpression)
):
    return _apply(
        ifilterfalse(lambda dec: isinstance(dec, ignore), declarations),
        symbol_table or SymbolTable((('__ statement __', _statement_func), ('__ expression __', _expression_func))),
        directives
    )


def expression(expr, symbol_table=None):
    symbol_table = symbol_table or SymbolTable((('__ expression __', _expression_func),))
    _ = symbol_table.setdefault('__ expression __', _expression_func)
    return _expression_func(expr, symbol_table)


def statement(stmnt, symbol_table=None):
    symbol_table = symbol_table or SymbolTable(
        (('__ expression __', _expression_func), ('__ statement __', _statement_func))
    )
    _ = symbol_table.setdefault('__ expression __', _expression_func)
    _ = symbol_table.setdefault('__ statement __', _statement_func)
    return _statement_func(stmnt, symbol_table)