__author__ = 'samyvilar'

from types import NoneType
from itertools import chain, izip, repeat, imap

from utils.sequences import peek, consume_all
from utils.rules import rules, set_rules

import front_end.parser.ast.declarations as declarations
import front_end.parser.ast.statements as statements
import front_end.parser.ast.expressions as expressions

from front_end.loader.locations import loc
from front_end.parser.types import c_type, FunctionType, VoidType, PointerType, ArrayType
import utils.symbol_table

from back_end.emitter.expressions.expression import expression
from back_end.emitter.statements.iteration import iteration_statement
from back_end.emitter.statements.jump import jump_statement, label_statement
from back_end.emitter.statements.selection import selection_statement


from back_end.emitter.expressions.cast import cast
from back_end.emitter.expressions.static import static_def_binaries, bind_load_address_func

from back_end.emitter.stack_state import stack_allocation, stack_de_allocation
from back_end.emitter.object_file import Data, Code

from back_end.emitter.c_types import size

from back_end.virtual_machine.instructions.architecture import Pass, Address, Offset
from back_end.virtual_machine.instructions.architecture import push, allocate, relative_jump, load_stack_pointer


def declaration(stmnt, symbol_table):
    # This are non-global declarations they don't require any space
    # but they could be referenced (extern, or function type)
    symbol_type = Code if isinstance(c_type(stmnt), FunctionType) else Data
    stmnt.symbol = symbol_type(declarations.name(stmnt), (), None, stmnt.storage_class, loc(stmnt))
    stmnt.symbol.size = size(c_type(stmnt), overrides={FunctionType: None})
    symbol_table[declarations.name(stmnt)] = stmnt
    yield Pass(loc(stmnt))


def static_definition(stmnt, symbol_table):
    def load_address(self, location):
        return push(Address(self._initial_data, location), location)

    data = static_def_binaries(stmnt, (Pass(loc(stmnt)),))
    stmnt._initial_data = peek(data)
    stmnt.end_of_data = Pass(loc(stmnt))
    stmnt.load_address = bind_load_address_func(load_address, stmnt)
    symbol_table[declarations.name(stmnt)] = stmnt
    return chain(  # jump over embedded data ...
        relative_jump(Offset(stmnt.end_of_data, loc(stmnt)), loc(stmnt)), consume_all(data), (stmnt.end_of_data,)
    )


def non_static_default_typed_definition(stmnt, symbol_table):
    return cast(
        symbol_table['__ expression __'](declarations.initialization(stmnt), symbol_table),
        c_type(declarations.initialization(stmnt)),
        c_type(stmnt),
        loc(stmnt)
    )


def non_static_pointer_typed_definition_initialized_by_array_type(stmnt, symbol_table):
    stack, expression = utils.symbol_table.get_symbols(symbol_table, '__ stack __', '__ expression __')
    expr = declarations.initialization(stmnt)
    assert not isinstance(expr, (expressions.Initializer, expressions.CompoundLiteral))
    return chain(  # evaluate stack expression, which will push values on the stack and initialized pointer with sp
        cast(expression(expr, symbol_table), c_type(expr), c_type(stmnt), loc(stmnt)), load_stack_pointer(loc(stmnt))
    )


def non_static_pointer_typed_definition(stmnt, symbol_table):
    return rules(non_static_pointer_typed_definition)[type(c_type(declarations.initialization(stmnt)))](
        stmnt, symbol_table
    )
set_rules(
    non_static_pointer_typed_definition,
    ((ArrayType, non_static_pointer_typed_definition_initialized_by_array_type),),
    non_static_default_typed_definition
)


def non_static_definition(stmnt, symbol_table):
    stmnt = stack_allocation(symbol_table['__ stack __'], stmnt)
    symbol_table[declarations.name(stmnt)] = stmnt
    return rules(non_static_definition)[type(c_type(stmnt))](stmnt, symbol_table)
set_rules(
    non_static_definition, ((PointerType, non_static_pointer_typed_definition),), non_static_default_typed_definition
)


def definition(stmnt, symbol_table):
    return rules(definition)[type(stmnt.storage_class)](stmnt, symbol_table)
non_static_storage_classes = declarations.Auto, declarations.Register, NoneType
set_rules(
    definition,
    chain(((declarations.Static, static_definition),), izip(non_static_storage_classes, repeat(non_static_definition)))
)


def compound_statement(stmnt, symbol_table):
    stack, statement = utils.symbol_table.get_symbols(symbol_table, '__ stack __', '__ statement __')
    stack_pointer, symbol_table = stack.stack_pointer, utils.symbol_table.push(symbol_table)
    for instr in chain.from_iterable(imap(statement, chain.from_iterable(stmnt), repeat(symbol_table))):
        yield instr
    for instr in allocate(stack.stack_pointer - stack_pointer, loc(stmnt)):  # deallocate any definitions that may occur
        yield instr
    stack.stack_pointer = (utils.symbol_table.pop(symbol_table) or True) and stack_pointer  # reset stack pointer ...


# Entry point to all statements, or statement expressions.
def statement(stmnt, symbol_table):
    is_expression = isinstance(stmnt, expressions.Expression)

    # Set entry point to False if its an expression or use statement function if present otherwise None.
    instrs = rules(statement)[type(stmnt)](stmnt, symbol_table)
    # Almost all Expression statements leave a value on the stack, so we must remove it.
    if stmnt and is_expression:
        instrs = chain(instrs, allocate(-size(c_type(stmnt), overrides={VoidType: 0}), loc(stmnt)))
    return instrs

statement_funcs = iteration_statement, jump_statement, selection_statement, label_statement
set_rules(
    statement,
    chain(
        (
            (declarations.EmptyDeclaration, lambda *_: ()),
            (statements.EmptyStatement, lambda *_: ()),
            (declarations.Declaration, declaration),
            (declarations.Definition, definition),
            (statements.CompoundStatement, compound_statement),
        ),
        chain.from_iterable(imap(izip, imap(rules, statement_funcs), imap(repeat, statement_funcs))),
        izip(rules(expression), repeat(expression))
    )
)