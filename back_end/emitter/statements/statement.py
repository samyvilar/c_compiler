__author__ = 'samyvilar'

from itertools import chain

from back_end.emitter.stack_state import Stack

from front_end.loader.locations import loc

import front_end.parser.ast.declarations as declarations
import front_end.parser.ast.statements as statements
import front_end.parser.ast.expressions as expressions
from front_end.parser.types import c_type, FunctionType
from front_end.parser.symbol_table import SymbolTable, push, pop


from back_end.emitter.statements.iteration import iteration_statement
from back_end.emitter.statements.jump import jump_statement, label_statement
from back_end.emitter.statements.selection import selection_statement
from back_end.emitter.expressions.expression import expression
from back_end.emitter.expressions.cast import cast

from back_end.emitter.stack_state import stack_allocation
from back_end.virtual_machine.instructions.architecture import Allocate, Integer, Pass, Address, Add, Push, RelativeJump

from back_end.emitter.c_types import size, binaries, bind_load_address_func

from back_end.emitter.object_file import Data, Code


# This are non-global declarations they don't require any space
# but they could be referenced (extern, or function type)
def declaration(stmnt, symbol_table, *_):
    symbol_type = Code if isinstance(c_type(stmnt), FunctionType) else Data
    stmnt.symbol = symbol_type(declarations.name(stmnt), (), size(c_type(stmnt)), stmnt.storage_class, loc(stmnt))
    symbol_table[declarations.name(stmnt)] = stmnt
    yield Pass(loc(stmnt))


def type_def(dec, *_):
    yield Pass(loc(dec))


def definition(stmnt, symbol_table, stack, *_):
    assert not isinstance(stmnt.storage_class, declarations.Extern) and size(c_type(stmnt))
    if isinstance(stmnt.storage_class, declarations.Static):  # Static Definition.
        start_of_data, end_of_data = Pass(loc(stmnt)), Pass(loc(stmnt))

        def load_address(self, location):
            yield Push(location, Address(self.start_of_data, location))
            yield Push(location, Integer(1, location))
            yield Add(location)

        stmnt.load_address = bind_load_address_func(stmnt, load_address)
        symbol_table[declarations.name(stmnt)] = stmnt
        instrs = chain((RelativeJump(loc(stmnt), Address(end_of_data, loc(stmnt))),), binaries(stmnt), (end_of_data,))
    else:  # Definition with either Auto/Register/None storage class.
        stmnt = stack_allocation(stack, stmnt)
        symbol_table[declarations.name(stmnt)] = stmnt
        # If definition is initialized simply evaluate the expression
        expr = declarations.initialization(stmnt)
        instrs = cast(expression(expr, symbol_table), c_type(expr), c_type(stmnt), loc(stmnt)) if expr \
            else (Allocate(loc(stmnt), size(c_type(stmnt))),)
    return instrs


def compound_statement(stmnt, symbol_table, stack, statement_func):
    stack_pointer = stack.stack_pointer
    symbol_table = push(symbol_table)
    for instr in chain.from_iterable(statement_func(s, symbol_table, stack) for st in stmnt for s in st):
        yield instr
    yield Allocate(loc(stmnt), Integer(stack.stack_pointer - stack_pointer, loc(stmnt)))
    _ = pop(symbol_table)
    stack.stack_pointer = stack_pointer


def _expression(expr, symbol_table, *_):
    return expression(expr, symbol_table)


# Entry point to all statements, or statement expressions.
def statement(stmnt, symbol_table=None, stack=None, statement_func=None):
    is_expression = isinstance(stmnt, expressions.Expression)
    symbol_table = symbol_table or SymbolTable()

    # Set entry point to expression or use statement function.
    instrs = statement.rules[type(stmnt)](
        stmnt,
        symbol_table,
        stack or Stack(),
        not is_expression and (statement_func or statement),
    )

    # All Expression statements leave a value on the stack, so we must remove it.
    if stmnt and is_expression and not statement_func:
        instrs = chain(instrs, (Allocate(loc(stmnt), Integer(-1 * size(c_type(stmnt)), loc(stmnt))),))
    return instrs
statement.rules = {
    declarations.EmptyDeclaration: lambda *args: (),
    declarations.TypeDef: type_def,
    declarations.Declaration: declaration,
    declarations.Definition: definition,
    statements.EmptyStatement: lambda *args: (),
    statements.CompoundStatement: compound_statement,
}
statement.rules.update({rule: iteration_statement for rule in iteration_statement.rules})
statement.rules.update({rule: jump_statement for rule in jump_statement.rules})
statement.rules.update({rule: selection_statement for rule in selection_statement.rules})
statement.rules.update({rule: label_statement for rule in label_statement.rules})
statement.rules.update({rule: _expression for rule in expression.rules})