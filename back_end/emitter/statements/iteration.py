__author__ = 'samyvilar'

from front_end.loader.locations import loc

from front_end.parser.ast.expressions import exp
from front_end.parser.ast.statements import ForStatement, WhileStatement, DoWhileStatement

from back_end.emitter.expressions.expression import expression
from back_end.virtual_machine.instructions.architecture import Address, Pass, JumpFalse, JumpTrue

from back_end.emitter.statements.jump import relative_jump_instrs


def for_statement(stmnt, symbol_table, stack, statement_func, jump_props):
    init_exp_bins = statement_func(stmnt.init_exp, symbol_table, stack, statement_func, jump_props)

    # The loop is an expression whose value should not be removed.
    loop_exp_bins = expression(exp(stmnt), symbol_table, stack, None, jump_props)

    upd_exp_bins = statement_func(stmnt.upd_exp, symbol_table, stack, statement_func, jump_props)

    current_depth = len(stack.saved_stack_pointers)  # break/continue need to know how many times to pop saved stack
    start_of_for_loop_instr, end_of_for_loop_instr = loop_exp_bins[0], Pass(loc(stmnt[-1]))

    for_body_bins = statement_func(
        stmnt.statement, symbol_table, stack, statement_func,
        jump_props=(start_of_for_loop_instr, end_of_for_loop_instr, current_depth)
    )

    complete_bins = init_exp_bins
    complete_bins.extend(loop_exp_bins)
    complete_bins.append(
        JumpFalse(loc(end_of_for_loop_instr), Address(end_of_for_loop_instr, loc(end_of_for_loop_instr)))
    )
    complete_bins.extend(for_body_bins)
    complete_bins.extend(upd_exp_bins)
    complete_bins.extend(relative_jump_instrs(Address(start_of_for_loop_instr, loc(start_of_for_loop_instr))))
    complete_bins.append(end_of_for_loop_instr)

    return complete_bins


def while_statement(stmnt, symbol_table, stack, statement_func, jump_props):
    exp_bins = expression(exp(stmnt), symbol_table, stack, None, jump_props)

    current_depth = len(stack.saved_stack_pointers)
    start_of_loop_instr, end_of_loop_instr = exp_bins[0], Pass(loc(stmnt.statement[-1]))

    while_body_bins = statement_func(
        stmnt.statement, symbol_table, statement_func,
        jump_props=(start_of_loop_instr, end_of_loop_instr, current_depth)
    )

    complete_bins = exp_bins
    complete_bins.append(JumpFalse(loc(exp(stmnt)), Address(end_of_loop_instr, loc(end_of_loop_instr))))
    complete_bins.extend(while_body_bins)
    complete_bins.extend(relative_jump_instrs(Address(start_of_loop_instr, loc(start_of_loop_instr))))
    complete_bins.append(end_of_loop_instr)

    return complete_bins


def do_while_statement(stmnt, symbol_table, stack, statement_func, jump_props):
    exp_bins = expression(exp(stmnt), symbol_table, stack, None, jump_props)

    current_depth = len(stack.saved_stack_pointers)
    start_of_loop_instr, end_of_loop_instr = Pass(loc(stmnt.statement)), Pass(loc(stmnt.statement[-1]))

    do_while_body_bins = statement_func(
        stmnt.statement, symbol_table, stack, statement_func,
        jump_props=(start_of_loop_instr, end_of_loop_instr, current_depth)
    )

    complete_bins = [start_of_loop_instr]
    complete_bins.extend(do_while_body_bins)
    complete_bins.extend(exp_bins)
    # noinspection PyTypeChecker
    complete_bins.append(JumpTrue(loc(exp_bins), Address(start_of_loop_instr, loc(exp_bins))))
    complete_bins.append(end_of_loop_instr)

    return complete_bins


def iteration_statement(stmnt, symbol_table, stack, statement_func, jump_props):
    return iteration_statement.rules[type(stmnt)](stmnt, symbol_table, stack, statement_func, jump_props)
iteration_statement.rules = {
    ForStatement: for_statement,
    WhileStatement: while_statement,
    DoWhileStatement: do_while_statement,
}
