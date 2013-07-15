__author__ = 'samyvilar'

from front_end.loader.locations import loc
from itertools import chain

from front_end.parser.symbol_table import push, pop
from front_end.parser.ast.expressions import exp
from front_end.parser.ast.statements import ForStatement, WhileStatement, DoWhileStatement

from back_end.emitter.expressions.expression import expression
from back_end.virtual_machine.instructions.architecture import Address, Pass, JumpFalse, JumpTrue, RelativeJump


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
        expression(exp(stmnt), symbol_table),  # loop invariant.
        (JumpFalse(loc(end_of_loop), Address(end_of_loop, loc(end_of_loop))),),

        loop_body(stmnt.statement, symbol_table, stack, statement_func, upd_expression, end_of_loop),

        (upd_expression,),
        statement_func(stmnt.upd_exp, symbol_table, stack),  # loop update.
        (RelativeJump(loc(stmnt), Address(start_of_loop, loc(start_of_loop))), end_of_loop)
    )


def while_statement(stmnt, symbol_table, stack, statement_func):
    start_of_loop, end_of_loop = Pass(loc(stmnt)), Pass(loc(stmnt))
    return chain(
        (start_of_loop,),
        expression(exp(stmnt), symbol_table),
        (JumpFalse(loc(exp(stmnt)), Address(end_of_loop, loc(end_of_loop))),),
        loop_body(stmnt.statement, symbol_table, stack, statement_func, start_of_loop, end_of_loop),
        (RelativeJump(loc(stmnt), Address(start_of_loop, loc(start_of_loop))), end_of_loop)
    )


def do_while_statement(stmnt, symbol_table, stack, statement_func):
    start_of_loop, end_of_loop = Pass(loc(stmnt)), Pass(loc(stmnt))

    def lazy(stmnt, symbol_table):  # TODO: find alternative ...
        yield expression(exp(stmnt), symbol_table)

    return chain(
        (start_of_loop,),
        loop_body(stmnt.statement, symbol_table, stack, statement_func, start_of_loop, end_of_loop),
        chain.from_iterable(lazy(stmnt, symbol_table)),
        (JumpTrue(loc(start_of_loop), Address(start_of_loop, loc(start_of_loop))), end_of_loop),
    )


def iteration_statement(stmnt, symbol_table, stack, statement_func):
    return iteration_statement.rules[type(stmnt)](stmnt, symbol_table, stack, statement_func)
iteration_statement.rules = {
    ForStatement: for_statement,
    WhileStatement: while_statement,
    DoWhileStatement: do_while_statement,
}
