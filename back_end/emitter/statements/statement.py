__author__ = 'samyvilar'

from itertools import chain, izip, repeat

from sequences import peek, takewhile

from types import NoneType

from back_end.emitter.stack_state import Stack

from front_end.loader.locations import loc

import front_end.parser.ast.declarations as declarations
import front_end.parser.ast.statements as statements
import front_end.parser.ast.expressions as expressions
from front_end.parser.types import c_type, FunctionType, VoidType
from front_end.parser.symbol_table import SymbolTable, push, pop


from back_end.emitter.statements.iteration import iteration_statement
from back_end.emitter.statements.jump import jump_statement, label_statement
from back_end.emitter.statements.selection import selection_statement
from back_end.emitter.expressions.expression import expression
from back_end.emitter.expressions.cast import cast

from back_end.emitter.stack_state import stack_allocation
from back_end.virtual_machine.instructions.architecture import allocate, Pass, Address, relative_jump, Byte, Offset
from back_end.virtual_machine.instructions.architecture import push as push_instr

from back_end.emitter.c_types import size, binaries, bind_load_address_func

from back_end.emitter.object_file import Data, Code


# This are non-global declarations they don't require any space
# but they could be referenced (extern, or function type)
def declaration(stmnt, symbol_table, *_):
    symbol_type = Code if isinstance(c_type(stmnt), FunctionType) else Data
    stmnt.symbol = symbol_type(declarations.name(stmnt), (), None, stmnt.storage_class, loc(stmnt))
    stmnt.symbol.size = (not isinstance(c_type(stmnt), FunctionType) and size(c_type(stmnt))) or None
    symbol_table[declarations.name(stmnt)] = stmnt
    yield Pass(loc(stmnt))


def type_def(dec, *_):
    yield Pass(loc(dec))


def static_definition(stmnt, symbol_table, *_):
    def load_address(self, location):
        return push_instr(Address(self._initial_data, location), location)

    data = binaries(stmnt)

    try:
        _initial_data = peek(data)
    except StopIteration:  # must be a zero size definition, give it one byte so we can at least address it ...
        _initial_data = Byte(loc(stmnt))
        data = (_initial_data,)

    stmnt._initial_data = _initial_data

    stmnt.end_of_data = Pass(loc(stmnt))
    stmnt.load_address = bind_load_address_func(load_address, stmnt)
    symbol_table[declarations.name(stmnt)] = stmnt
    if not isinstance(declarations.initialization(stmnt), (expressions.ConstantExpression, NoneType)):
        raise ValueError('{l} Static definitions may only be initialized with a ConstantExpression got {g}'.format(
            l=loc(stmnt), g=declarations.initialization(stmnt)
        ))
    return chain(
        relative_jump(Offset(stmnt.end_of_data, loc(stmnt)), loc(stmnt)),
        takewhile(None, data),
        (stmnt.end_of_data,)
    )


def non_static_definition(stmnt, symbol_table, stack, *_):
    stmnt = stack_allocation(stack, stmnt)
    symbol_table[declarations.name(stmnt)] = stmnt
    # If definition is initialized simply evaluate the expression, otherwise allocate space on the stack.
    expr = declarations.initialization(stmnt)
    return (expr and cast(expression(expr, symbol_table), c_type(expr), c_type(stmnt), loc(stmnt))) or \
        allocate(size(c_type(stmnt)), loc(stmnt))


def definition(stmnt, symbol_table, stack, *_):
    return definition.rules[type(stmnt.storage_class)](stmnt, symbol_table, stack, _)
definition.rules = {
    declarations.Static: static_definition,
    declarations.Auto: non_static_definition,
    declarations.Register: non_static_definition,
    NoneType: non_static_definition
}


def compound_statement(stmnt, symbol_table, stack, statement_func):
    stack_pointer, symbol_table = stack.stack_pointer, push(symbol_table)
    for instr in chain(chain.from_iterable(statement_func(s, symbol_table, stack) for s in chain.from_iterable(stmnt))):
        yield instr
    for instr in allocate(stack.stack_pointer - stack_pointer, loc(stmnt)):
        yield instr
    stack.stack_pointer, _ = stack_pointer, pop(symbol_table)


def _expression(expr, symbol_table, stack, *_):
    return expression(expr, symbol_table)


# Entry point to all statements, or statement expressions.
def statement(stmnt, symbol_table=None, stack=None, statement_func=None):
    is_expression = isinstance(stmnt, expressions.Expression)

    # Set entry point to expression or use statement function.
    instrs = statement.rules[type(stmnt)](
        stmnt,
        symbol_table or SymbolTable(),
        stack or Stack(),
        not is_expression and (statement_func or statement),
    )

    # Almost all Expression statements leave a value on the stack, so we must remove it.
    if stmnt and is_expression and not statement_func and not isinstance(c_type(stmnt), VoidType):
        instrs = chain(instrs, allocate(-size(c_type(stmnt)), loc(stmnt)))
    return instrs
statement.rules = {
    declarations.EmptyDeclaration: lambda *args: (),
    declarations.TypeDef: type_def,
    declarations.Declaration: declaration,
    declarations.Definition: definition,
    statements.EmptyStatement: lambda *args: (),
    statements.CompoundStatement: compound_statement,
}
statement.rules.update(chain(
    izip(iteration_statement.rules, repeat(iteration_statement)),
    izip(jump_statement.rules, repeat(jump_statement)),
    izip(selection_statement.rules, repeat(selection_statement)),
    izip(label_statement.rules, repeat(label_statement)),
    izip(expression.rules, repeat(_expression)),
))