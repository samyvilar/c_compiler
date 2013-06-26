__author__ = 'samyvilar'

from collections import defaultdict
from copy import deepcopy

from back_end.emitter.types import flatten
from front_end.loader.locations import loc
from front_end.parser.ast.expressions import exp
from front_end.parser.ast.statements import IfStatement, SwitchStatement, CaseStatement, DefaultStatement

from back_end.emitter.expressions.expression import expression
from back_end.virtual_machine.instructions.architecture import Pass, JumpFalse, Address, JumpTable, Instruction

from back_end.emitter.statements.jump import relative_jump_instrs
from back_end.emitter.statements.jump import patch_goto_instrs


def if_statement(stmnt, symbol_table, stack, statement_func, jump_props):
    exp_bins = expression(exp(stmnt), symbol_table, stack)
    body_bins = statement_func(stmnt.statement, symbol_table, stack, statement_func, jump_props)
    end_of_if_instruction = Pass(loc(stmnt.statement))

    else_body_bins = ()
    if stmnt.else_statement:
        else_body_bins = [end_of_if_instruction]
        else_body_bins.extend(statement_func(
            stmnt.else_statement.statement, symbol_table, stack, statement_func, jump_props
        ))
        location = loc(stmnt.else_statement)
        else_body_bins.append(Pass(location))
        body_bins.extend(relative_jump_instrs(Address(else_body_bins[-1], location)))
    else:
        body_bins.append(end_of_if_instruction)

    complete_bins = exp_bins
    complete_bins.append(JumpFalse(loc(exp(stmnt)), Address(end_of_if_instruction, loc(end_of_if_instruction))))
    complete_bins.extend(body_bins)
    complete_bins.extend(else_body_bins)

    return complete_bins


def case_statement(stmnt, symbol_table, stack, statement_func, jump_props):
    binaries = [Pass(loc(stmnt))]  # Blank instruction between empty case cascades, in order to avoid recursive calls
    stmnt.stack = deepcopy(stack)  # case statements may be placed in nested compound statements.
    binaries[0].case = stmnt
    binaries.extend(statement_func(stmnt.statement, symbol_table, stack, statement_func, jump_props))
    return binaries


def switch_statement(stmnt, symbol_table, stack, statement_func, jump_props):
    exp_bins = expression(exp(stmnt), symbol_table, stack)
    end_switch = Pass(stmnt.statement and loc(stmnt.statement[-1]) or loc(stmnt))
    stmnt.stack = deepcopy(stack)
    # if switch inside loop, only update end_instruct, since continue jumps to start of loop break goes to end of switch
    jump_props = (jump_props[0], end_switch, jump_props[2]) if jump_props else (None, end_switch, len(stack))

    default = None
    body_bins = []
    allocation_table = []
    cases = defaultdict(lambda: Address(end_switch, loc(end_switch)))
    for instr in flatten(statement_func(stmnt.statement, symbol_table, stack, statement_func, jump_props), Instruction):
        if hasattr(instr, 'case'):
            allocation_table.append(
                patch_goto_instrs(stmnt, instr.case) + relative_jump_instrs(Address(instr, loc(instr)))
            )
            addr = Address(allocation_table[-1][0], loc(instr))
            if isinstance(instr.case, DefaultStatement):
                assert default is None
                cases.default_factory = lambda: addr
                default = True
            else:
                assert isinstance(instr.case, CaseStatement)
                cases[exp(exp(instr.case))] = addr
        body_bins.append(instr)

    complete_bins = []
    complete_bins.extend(exp_bins)
    complete_bins.append(JumpTable(loc(stmnt), cases))
    complete_bins.extend(allocation_table)
    complete_bins.extend(body_bins)
    complete_bins.append(end_switch)

    return complete_bins


def selection_statement(stmnt, symbol_table, stack, statement_func, jump_props):
    return selection_statement.rules[type(stmnt)](stmnt, symbol_table, stack, statement_func, jump_props)
selection_statement.rules = {
    IfStatement: if_statement,
    SwitchStatement: switch_statement,
    CaseStatement: case_statement,
    DefaultStatement: case_statement,
}
