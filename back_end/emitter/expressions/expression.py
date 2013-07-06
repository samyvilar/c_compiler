__author__ = 'samyvilar'

from itertools import chain

from front_end.loader.locations import loc

from front_end.parser.symbol_table import SymbolTable

from front_end.parser.ast.declarations import name
from front_end.parser.ast.expressions import ConstantExpression, CastExpression, IdentifierExpression
from front_end.parser.ast.expressions import BinaryExpression, AssignmentExpression, CompoundAssignmentExpression
from front_end.parser.ast.expressions import EmptyExpression
from front_end.parser.types import c_type, FunctionType, ArrayType

from back_end.emitter.instructions.stack_state import Stack

from back_end.emitter.expressions.cast import cast_expression
from back_end.emitter.expressions.constant import constant_expression
from back_end.emitter.expressions.binary import binary_expression
from back_end.emitter.expressions.unary import unary_expression
from back_end.emitter.expressions.postfix import postfix_expression

from back_end.emitter.types import size

from back_end.virtual_machine.instructions.architecture import Load


def identifier_expression(expr, symbol_table, expression_func):
    # Defaults to Load, assignment expression will update it to set.
    symbol = symbol_table[name(expr)]
    if isinstance(c_type(symbol), (FunctionType, ArrayType)):  # Function/Array Types are nothing the addresses.
        return symbol.load_address(loc(expr))
    return chain(symbol.load_address(loc(expr)), (Load(loc(expr), size(c_type(expr))),),)


# Entry point to all expression or expression statements
def expression(expr, symbol_table=None, expression_func=None):
    instrs = expression.rules[type(expr)](
        expr,
        symbol_table or SymbolTable(),
        expression_func or expression,
    )
    # Every other recursive call to expression uses expression_func as expression
    # Entry point even from statement will set expression_func to false/None.
    if not expression_func:  # Append postfix instrs
        instrs = chain(instrs, postfix_expression.late_instrs)

    return instrs
expression.rules = {
    EmptyExpression: lambda expr, *_: (),
    ConstantExpression: constant_expression,
    CastExpression: cast_expression,
    IdentifierExpression: identifier_expression,

    BinaryExpression: binary_expression,
    AssignmentExpression: binary_expression,
    CompoundAssignmentExpression: binary_expression,
}
expression.rules.update({rule: unary_expression for rule in unary_expression.rules})
expression.rules.update({rule: postfix_expression for rule in postfix_expression.rules})