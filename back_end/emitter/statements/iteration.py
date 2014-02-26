__author__ = 'samyvilar'

from itertools import chain, imap, repeat

from utils.rules import set_rules, rules
from front_end.loader.locations import loc
from utils.symbol_table import push, pop
from front_end.parser.ast.expressions import exp
from front_end.parser.ast.statements import ForStatement, WhileStatement, DoWhileStatement
from back_end.virtual_machine.instructions.architecture import Offset, Pass, relative_jump
from back_end.virtual_machine.instructions.architecture import get_jump_false, get_jump_true
from back_end.emitter.c_types import c_type, size_arrays_as_pointers


def loop_body(body, symbol_table, continue_instr, break_instr):
    symbol_table = push(symbol_table)
    statement, stack = imap(symbol_table.__getitem__, ('__ statement __', '__ stack __'))
    symbol_table['__ continue __'] = (continue_instr, stack.stack_pointer)
    symbol_table['__ break __'] = (break_instr, stack.stack_pointer)
    for instr in statement(body, symbol_table):
        yield instr
    _ = pop(symbol_table)


def for_statement(stmnt, symbol_table):
    start_of_loop, end_of_loop, upd_expression = imap(Pass, repeat(loc(stmnt), 3))
    expression, statement, stack = imap(
        symbol_table.__getitem__, ('__ expression __', '__ statement __', '__ stack __')
    )
    return chain(
        statement(stmnt.init_exp, symbol_table),  # loop initialization.
        (start_of_loop,),  # start of conditional

        # loop invariant.
        get_jump_false(size_arrays_as_pointers(c_type(exp(stmnt))))(
            expression(exp(stmnt), symbol_table), Offset(end_of_loop, loc(end_of_loop)), loc(stmnt)
        ),

        loop_body(stmnt.statement, symbol_table, upd_expression, end_of_loop),

        (upd_expression,),
        statement(stmnt.upd_exp, symbol_table),  # loop update.
        relative_jump(Offset(start_of_loop, loc(start_of_loop)), loc(stmnt)),
        (end_of_loop,)
    )


def while_statement(stmnt, symbol_table):
    start_of_loop, end_of_loop = imap(Pass, repeat(loc(stmnt), 2))
    return chain(
        (start_of_loop,),
        get_jump_false(size_arrays_as_pointers(c_type(exp(stmnt))))(
            symbol_table['__ expression __'](exp(stmnt), symbol_table), Offset(end_of_loop, loc(end_of_loop)), loc(end_of_loop)
        ),
        loop_body(stmnt.statement, symbol_table, start_of_loop, end_of_loop),
        relative_jump(Offset(start_of_loop, loc(start_of_loop)), loc(end_of_loop)),
        (end_of_loop,)
    )


def do_while_statement(stmnt, symbol_table):
    start_of_loop, end_of_loop = Pass(loc(stmnt)), Pass(loc(stmnt))
    yield start_of_loop  # do while loops contain the update expression after their body ...
    for instr in loop_body(stmnt.statement, symbol_table, start_of_loop, end_of_loop):
        yield instr
    for instr in get_jump_true(size_arrays_as_pointers(c_type(exp(stmnt))))(
            symbol_table['__ expression __'](exp(stmnt), symbol_table),
            Offset(start_of_loop, loc(start_of_loop)),
            loc(start_of_loop)
    ):
        yield instr
    yield end_of_loop


def iteration_statement(stmnt, symbol_table):
    return rules(iteration_statement)[type(stmnt)](stmnt, symbol_table)
set_rules(
    iteration_statement,
    ((ForStatement, for_statement), (WhileStatement, while_statement), (DoWhileStatement, do_while_statement))
)
