__author__ = 'samyvilar'

from front_end.loader.locations import loc

from itertools import chain

import front_end.parser.ast.declarations as declarations
import front_end.parser.ast.statements as statements
import front_end.parser.ast.expressions as expressions
from front_end.parser.types import c_type, FunctionType
from front_end.parser.symbol_table import SymbolTable, push, pop

from back_end.emitter.instructions.stack_state import Stack

from back_end.emitter.statements.iteration import iteration_statement
from back_end.emitter.statements.jump import jump_statement
from back_end.emitter.statements.selection import selection_statement
from back_end.emitter.statements.label import label_statement
from back_end.emitter.expressions.expression import expression
from back_end.emitter.expressions.cast import cast

from back_end.emitter.instructions.stack_state import stack_allocation
from back_end.emitter.instructions.data import global_allocation
from back_end.virtual_machine.instructions.architecture import SaveStackPointer, RestoreStackPointer, Allocate, Integer
from back_end.virtual_machine.instructions.architecture import Pass

from back_end.emitter.types import size, binaries

from back_end.emitter.object_file import Data, Code


# This are non-global declarations they don't require any space
# but they could be referenced (extern, or function type)
def declaration(stmnt, symbol_table, stack, statement_func, jump_props):
    symbol_type = Code if isinstance(c_type(stmnt), FunctionType) else Data
    stmnt.symbol = symbol_type(declarations.name(stmnt), (), size(c_type(stmnt)), stmnt.storage_class, loc(stmnt))
    symbol_table[declarations.name(stmnt)] = stmnt
    yield Pass(loc(stmnt))


def type_def(dec, symbol_table, *_):
    symbol_table[declarations.name(dec)] = c_type(dec)
    yield Pass(loc(dec))


def definition(stmnt, symbol_table, stack, statement_func, jump_props):
    if isinstance(stmnt.storage_class, declarations.Static):  # Static Definition.
        stmnt = global_allocation(stmnt)
        symbol = stmnt.symbol = Data(  # All non-global definition are Data type (no nested functions).
            declarations.name(stmnt),
            binaries(stmnt),  # Initialized to 0
            size(c_type(stmnt)),
            stmnt.storage_class,
            loc(stmnt),
        )
        yield symbol
    else:  # Definition with either Auto/Register/None storage class.
        stmnt = stack_allocation(stack, stmnt)
        symbol_table[declarations.name(stmnt)] = stmnt
        # If definition is initialized simply evaluate the expression
        if declarations.initialization(stmnt):
            for instr in cast(
                expression(declarations.initialization(stmnt), symbol_table),
                c_type(declarations.initialization(stmnt)),
                c_type(stmnt),
                loc(stmnt)
            ):
                yield instr
        else:
            yield Allocate(loc(stmnt), size(c_type(stmnt)))


def push_instrs(symbol_table, stack, location):
    stack.save_stack_pointer()
    _ = push(symbol_table)
    yield SaveStackPointer(location)


def pop_instrs(symbol_table, stack, location):
    stack.restore_stack_pointer()
    _ = pop(symbol_table)
    yield RestoreStackPointer(location)


def compound_statement(stmnt, symbol_table, stack, statement_func, jump_props):
    return chain(
        push_instrs(symbol_table, stack, loc(stmnt)),
        chain.from_iterable(
            (statement_func(s, symbol_table, stack, None, jump_props) for st in stmnt for s in st)
        ),
        pop_instrs(symbol_table, stack, loc(stmnt)),
    )


def _expression(expr, symbol_table, *_):
    return expression(expr, symbol_table)


# Entry point to all statements, or statement expressions.
def statement(stmnt, symbol_table=None, stack=None, statement_func=None, jump_props=()):
    is_expression = isinstance(stmnt, expressions.Expression)
    symbol_table = symbol_table or SymbolTable()

    # Set entry point to expression or use statement function.
    instrs = statement.rules[type(stmnt)](
        stmnt,
        symbol_table,
        stack or Stack(),
        not is_expression and (statement_func or statement),
        jump_props,
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