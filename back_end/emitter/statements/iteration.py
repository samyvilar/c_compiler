__author__ = 'samyvilar'

from front_end.loader.locations import loc
from itertools import chain

from front_end.parser.ast.expressions import exp
from front_end.parser.ast.statements import ForStatement, WhileStatement, DoWhileStatement

from back_end.emitter.expressions.expression import expression
from back_end.virtual_machine.instructions.architecture import Address, Pass, JumpFalse, JumpTrue

from back_end.emitter.statements.jump import relative_jump_instrs


def for_statement(stmnt, symbol_table, stack, statement_func, jump_props):
    start_of_loop, end_of_for_loop_instr, upd_expression = Pass(loc(stmnt)), Pass(loc(stmnt)), Pass(loc(stmnt))
    return chain(
        statement_func(stmnt.init_exp, symbol_table, stack),  # loop initialization.
        (start_of_loop,),  # start of conditional
        expression(exp(stmnt), symbol_table),  # loop invariant.
        (JumpFalse(loc(end_of_for_loop_instr), Address(end_of_for_loop_instr, loc(end_of_for_loop_instr))),),
        statement_func(  # body of loop
            stmnt.statement,
            symbol_table,
            stack,
            statement_func,
            jump_props=(upd_expression, end_of_for_loop_instr, len(stack))
        ),
        (upd_expression,),
        statement_func(stmnt.upd_exp, symbol_table, stack),  # loop update.
        relative_jump_instrs(Address(start_of_loop, loc(start_of_loop))),
        (end_of_for_loop_instr,)
    )


def while_statement(stmnt, symbol_table, stack, statement_func, jump_props):
    start_of_loop, end_of_loop = Pass(loc(stmnt)), Pass(loc(stmnt))
    return chain(
        (start_of_loop,),
        expression(exp(stmnt), symbol_table),
        (JumpFalse(loc(exp(stmnt)), Address(end_of_loop, loc(end_of_loop))),),
        statement_func(
            stmnt.statement,
            symbol_table,
            stack,
            statement_func,
            jump_props=(start_of_loop, end_of_loop, len(stack))
        ),
        relative_jump_instrs(Address(start_of_loop, loc(start_of_loop))),
        (end_of_loop,)
    )


def do_while_statement(stmnt, symbol_table, stack, statement_func, jump_props):
    start_of_loop, end_of_loop = Pass(loc(stmnt)), Pass(loc(stmnt))

    def lazy_eval(stmnt, symbol_table):  # TODO: find alternative ...
        yield expression(exp(stmnt), symbol_table)

    return chain(
        (start_of_loop,),
        statement_func(
            stmnt.statement,
            symbol_table,
            stack,
            statement_func,
            jump_props=(start_of_loop, end_of_loop, len(stack))
        ),
        chain.from_iterable(lazy_eval(stmnt, symbol_table)),
        (JumpTrue(loc(start_of_loop), Address(start_of_loop, loc(start_of_loop))), end_of_loop),
    )


def iteration_statement(stmnt, symbol_table, stack, statement_func, jump_props):
    return iteration_statement.rules[type(stmnt)](stmnt, symbol_table, stack, statement_func, jump_props)
iteration_statement.rules = {
    ForStatement: for_statement,
    WhileStatement: while_statement,
    DoWhileStatement: do_while_statement,
}
