__author__ = 'samyvilar'

from copy import deepcopy

from front_end.loader.locations import loc
from front_end.parser.ast.declarations import name
from front_end.parser.ast.statements import LabelStatement

from back_end.virtual_machine.instructions.architecture import Pass


def label_statement(stmnt, symbol_table, stack, statement_func, jump_props):
    stmnt.stack = deepcopy(stack)  # copy stack TODO: find optimal method of saving the stack state, deepcopy expensive
    stmnt.instr = [Pass(loc(stmnt))]
    stmnt.instr.extend(statement_func(stmnt.statement, symbol_table, stack, statement_func, jump_props))
    symbol_table[name(stmnt)] = stmnt  # Add Label to list of all labels.
    return stmnt.instr
label_statement.rules = {LabelStatement}
