__author__ = 'samyvilar'

from itertools import chain
from collections import deque

from front_end.loader.locations import loc

from front_end.parser.ast.declarations import name
from front_end.parser.ast.expressions import ConstantExpression, CastExpression, IdentifierExpression
from front_end.parser.ast.expressions import BinaryExpression, AssignmentExpression, CompoundAssignmentExpression
from front_end.parser.ast.expressions import PostfixIncrementExpression, PostfixDecrementExpression
from front_end.parser.ast.expressions import EmptyExpression, exp
from front_end.parser.types import c_type, FunctionType, ArrayType, VoidPointer

from back_end.emitter.expressions.cast import cast_expression
from back_end.emitter.expressions.constant import constant_expression
from back_end.emitter.expressions.binary import binary_expression
from back_end.emitter.expressions.unary import unary_expression
from back_end.emitter.expressions.postfix import postfix_expression
from back_end.emitter.expressions.ternary import ternary_expression

from back_end.emitter.c_types import size

from back_end.virtual_machine.instructions.architecture import Load, Address, Integer, Set, Add, Allocate, Push
from back_end.virtual_machine.instructions.architecture import Dequeue


def identifier_expression(expr, symbol_table, expression_func):
    # Defaults to Load, assignment expression will update it to set.
    dec = symbol_table[name(expr)]
    if isinstance(c_type(dec), (FunctionType, ArrayType)):  # Function/Array Types are nothing more than addresses.
        return dec.load_address(loc(expr))
    return chain(dec.load_address(loc(expr)), (Load(loc(expr), size(c_type(expr))),),)


def postfix_inc_dec(expr, value):
    yield Dequeue(loc(expr), size(VoidPointer))
    yield Load(loc(expr), size(c_type(expr)))
    yield Push(loc(expr), Integer(value, loc(expr)))
    yield Add(loc(expr))
    yield Dequeue(loc(expr), size(VoidPointer))
    yield Set(loc(expr), size(c_type(expr)))
    yield Allocate(loc(expr), Integer(-1 * size(c_type(expr)), loc(expr)))


# Entry point to all expression or expression statements
def expression(expr, symbol_table=None, expression_func=None):
    symbol_table = symbol_table or {}
    instrs = expression.rules[type(expr)](expr, symbol_table, expression_func or expression)

    if '__ LATE INSTRS __' not in symbol_table:
        symbol_table.setdefault('__ LATE INSTRS __', deque())

    # Every other recursive call to expression uses expression_func as expression
    # Entry point even from statement will set expression_func to false/None.
    if isinstance(expr, (PostfixIncrementExpression, PostfixDecrementExpression)):
        symbol_table['__ LATE INSTRS __'].append(
            postfix_inc_dec(exp(expr), 1 if isinstance(expr, PostfixIncrementExpression) else -1)
        )
    if not expression_func:  # Append postfix instrs
        instrs = chain(instrs, chain.from_iterable(symbol_table.pop('__ LATE INSTRS __')))

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
expression.rules.update({rule: ternary_expression for rule in ternary_expression.rules})
