__author__ = 'samyvilar'

from front_end.loader.locations import loc
from itertools import chain

from front_end.parser.symbol_table import push, pop
from front_end.parser.ast.expressions import exp
from front_end.parser.ast.statements import ForStatement, WhileStatement, DoWhileStatement

from back_end.emitter.expressions.expression import expression
from back_end.virtual_machine.instructions.architecture import Address, Pass, jump_false, jump_true, relative_jump


def loop_body(body, symbol_table, stack, statement_func, continue_instr, break_instr):
    symbol_table = push(symbol_table)
    symbol_table['__ continue __'] = (continue_instr, stack.stack_pointer)
    symbol_table['__ break __'] = (break_instr, stack.stack_pointer)
    for instr in statement_func(body, symbol_table, stack):
        yield instr
    _ = pop(symbol_table)


def for_statement(stmnt, symbol_table, stack, statement_func):
    start_of_loop, end_of_loop, upd_expression = Pass(loc(stmnt)), Pass(loc(stmnt)), Pass(loc(stmnt))

    return chain(
        statement_func(stmnt.init_exp, symbol_table, stack),  # loop initialization.
        (start_of_loop,),  # start of conditional

        # loop invariant.
        jump_false(expression(exp(stmnt), symbol_table), Address(end_of_loop, loc(end_of_loop)), loc(stmnt)),

        loop_body(stmnt.statement, symbol_table, stack, statement_func, upd_expression, end_of_loop),

        (upd_expression,),
        statement_func(stmnt.upd_exp, symbol_table, stack),  # loop update.
        relative_jump(Address(start_of_loop, loc(start_of_loop)), loc(stmnt)),
        (end_of_loop,)
    )


def while_statement(stmnt, symbol_table, stack, statement_func):
    start_of_loop, end_of_loop = Pass(loc(stmnt)), Pass(loc(stmnt))
    return chain(
        (start_of_loop,),
        jump_false(expression(exp(stmnt), symbol_table), Address(end_of_loop, loc(end_of_loop)), loc(end_of_loop)),
        loop_body(stmnt.statement, symbol_table, stack, statement_func, start_of_loop, end_of_loop),
        relative_jump(Address(start_of_loop, loc(start_of_loop)), loc(end_of_loop)),
        (end_of_loop,)
    )


def do_while_statement(stmnt, symbol_table, stack, statement_func):
    start_of_loop, end_of_loop = Pass(loc(stmnt)), Pass(loc(stmnt))

    yield start_of_loop
    for instr in loop_body(stmnt.statement, symbol_table, stack, statement_func, start_of_loop, end_of_loop):
        yield instr
    for instr in jump_true(
            expression(exp(stmnt), symbol_table),
            Address(start_of_loop, loc(start_of_loop)),
            loc(start_of_loop)
    ):
        yield instr
    yield end_of_loop


def iteration_statement(stmnt, symbol_table, stack, statement_func):
    return iteration_statement.rules[type(stmnt)](stmnt, symbol_table, stack, statement_func)
iteration_statement.rules = {
    ForStatement: for_statement,
    WhileStatement: while_statement,
    DoWhileStatement: do_while_statement,
}
