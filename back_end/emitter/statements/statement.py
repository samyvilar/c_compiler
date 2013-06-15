__author__ = 'samyvilar'

from front_end.loader.locations import loc

import front_end.parser.ast.declarations as declarations
import front_end.parser.ast.statements as statements
import front_end.parser.ast.expressions as expressions
from front_end.parser.types import c_type, FunctionType
from front_end.parser.symbol_table import SymbolTable

from back_end.emitter.instructions.stack_state import Stack

from back_end.emitter.statements.iteration import iteration_statement
from back_end.emitter.statements.jump import jump_statement
from back_end.emitter.statements.selection import selection_statement
from back_end.emitter.statements.label import label_statement
from back_end.emitter.expressions.expression import expression

from back_end.emitter.instructions.stack_state import stack_allocation
from back_end.emitter.instructions.data import global_allocation
from back_end.virtual_machine.instructions.architecture import SaveStackPointer, RestoreStackPointer, Allocate, Integer

from back_end.emitter.types import size, binaries

from back_end.emitter.object_file import Data, Code


# This are non-global declarations they don't require any space
# but they could be referenced (extern, or function type)
def declaration(stmnt, symbol_table, stack, statement_func, jump_props):
    symbol_type = Code if isinstance(c_type(stmnt), FunctionType) else Data
    stmnt.symbol = symbol_type(declarations.name(stmnt), (), size(c_type(stmnt)), stmnt.storage_class, loc(stmnt))
    symbol_table[declarations.name(stmnt)] = stmnt
    return stmnt.symbol


def type_def(stmnt, symbol_table, stack, statement_func, jump_props):
    symbol_table[declarations.name(stmnt)] = stmnt


def definition(stmnt, symbol_table, stack, statement_func, jump_props):
    if isinstance(stmnt.storage_class, declarations.Static):  # Static Definition.
        stmnt = global_allocation(stmnt)
        symbol = stmnt.symbol = Data(  # All non-global definition are Data type (no nested functions.)
            declarations.name(stmnt),
            binaries(stmnt),  # Initialized to 0
            size(c_type(stmnt)),
            stmnt.storage_class,
            loc(stmnt),
        )
    else:  # Either Auto/Register Definition.
        stmnt = stack_allocation(stack, stmnt)
        # If definition is initialized simply evaluate the expression
        symbol = declarations.initialization(stmnt) and (  # gen instructions if definition is initialized.
            statement_func(
                declarations.initialization(stmnt),
                symbol_table,
                stack,
                statement_func,
                jump_props
            )
        ) or [Allocate(loc(stmnt), size(c_type(stmnt)))]  # Else just allocate.

    symbol_table[declarations.name(stmnt)] = stmnt
    return symbol


def compound_statement(stmnt, symbol_table, stack, statement_func, jump_props):
    stack.save_stack_pointer()
    binaries = [SaveStackPointer(loc(stmnt))]
    for st in stmnt:
        binaries.append(statement_func(st, symbol_table, stack, statement_func, jump_props))
    # noinspection PyTypeChecker
    binaries.append(RestoreStackPointer(loc(stmnt)))
    stack.restore_stack_pointer()

    return binaries


# Entry point to all statements, or statement expressions.
def statement(stmnt, symbol_table=None, stack=None, statement_func=None, jump_props=()):
    is_expression = isinstance(stmnt, expressions.Expression)

    # Set entry point to expression or use statement function.
    instrs = statement.rules[type(stmnt)](
        stmnt,
        symbol_table or SymbolTable(),
        stack or Stack(),
        not is_expression and (statement_func or statement),
        jump_props,
    )

    # All Expression statement leave a value on the stack, so we must remove it.
    if instrs and is_expression:
        instrs.append(Allocate(loc(stmnt), Integer(-1 * size(c_type(stmnt)), loc(stmnt))))

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
statement.rules.update({rule: expression for rule in expression.rules})