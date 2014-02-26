__author__ = 'samyvilar'

from itertools import chain, imap
from copy import deepcopy

from utils.rules import set_rules, rules
from front_end.loader.locations import loc
from utils.symbol_table import push, pop
from front_end.parser.ast.expressions import exp
from front_end.parser.ast.statements import IfStatement, SwitchStatement, CaseStatement, DefaultStatement
from front_end.parser.types import IntegralType, c_type

from back_end.virtual_machine.instructions.architecture import Pass, Offset, relative_jump, get_jump_false, jump_table

from back_end.emitter.c_types import size_arrays_as_pointers
from back_end.emitter.statements.jump import update_stack

from utils.errors import raise_error, error_if_not_type


def if_statement(stmnt, symbol_table):
    end_of_if, end_of_else = Pass(loc(stmnt)), Pass(loc(stmnt))
    expression, statement = imap(symbol_table.__getitem__, ('__ expression __', '__ statement __'))
    for instr in chain(
        get_jump_false(size_arrays_as_pointers(c_type(exp(stmnt))))(
            expression(exp(stmnt), symbol_table), Offset(end_of_if, loc(end_of_if)), loc(end_of_if)
        ),
        statement(stmnt.statement, symbol_table)
    ):
        yield instr

    else_stmnt = stmnt.else_statement.statement
    if else_stmnt:
        for instr in chain(
            relative_jump(Offset(end_of_else, loc(end_of_else)), loc(stmnt)),
            (end_of_if,),
            statement(else_stmnt, symbol_table),
            (end_of_else,),
        ):
            yield instr
    else:
        yield end_of_if


def case_statement(stmnt, symbol_table):
    try:
        _ = symbol_table['__ switch __']
    except KeyError as _:
        raise ValueError('{l} case statement outside switch statement'.format(l=loc(stmnt)))
    initial_instr = Pass(loc(stmnt))
    stmnt.stack = deepcopy(symbol_table['__ stack __'])  # case statements may be placed in nested compound statements.
    initial_instr.case = stmnt
    return chain((initial_instr,), symbol_table['__ statement __'](stmnt.statement, symbol_table))


def switch_statement(stmnt, symbol_table):
    _ = (not isinstance(c_type(exp(stmnt)), IntegralType)) and raise_error(
        '{l} Expected an integral type got {g}'.format(g=c_type(exp(stmnt)), l=loc(stmnt))
    )

    end_switch = Pass(loc(stmnt))
    stmnt.stack = deepcopy(symbol_table['__ stack __'])

    # if switch inside loop, only update end_instruct, since continue jumps to start of loop break goes to end of switch
    def body(stmnt, symbol_table, end_switch):
        symbol_table = push(symbol_table)
        stack, statement = imap(symbol_table.__getitem__, ('__ stack __', '__ statement __'))
        symbol_table['__ break __'] = (end_switch, stack.stack_pointer)
        symbol_table['__ switch __'] = True

        allocation_table = []  # create an allocation table to update stack before jump in case of nested definitions
        switch_body_instrs = []
        cases = {'default': Offset(end_switch, loc(stmnt))}

        for instr in statement(stmnt.statement, symbol_table):
            if isinstance(getattr(instr, 'case', None), CaseStatement):
                start = Pass(loc(instr))
                allocation_table.append(
                    chain(
                        (start,),
                        update_stack(stmnt.stack.stack_pointer, instr.case.stack.stack_pointer, loc(instr)),
                        relative_jump(Offset(instr, loc(instr)), loc(instr)),
                    )
                )

                cases[error_if_not_type(exp(exp(instr.case)), (int, long, str))] = Offset(start, loc(instr))
                del instr.case
            switch_body_instrs.append(instr)

        max_switch_value = 2**(8*size_arrays_as_pointers(c_type(exp(stmnt)))) - 1
        for instr in jump_table(loc(stmnt), cases, allocation_table, max_switch_value, switch_body_instrs):
            yield instr
        _ = pop(symbol_table)

    return chain(
        symbol_table['__ expression __'](exp(stmnt), symbol_table), body(stmnt, symbol_table, end_switch), (end_switch,)
    )


def selection_statement(stmnt, symbol_table):
    return rules(selection_statement)[type(stmnt)](stmnt, symbol_table)
set_rules(
    selection_statement,
    (
        (IfStatement, if_statement), (SwitchStatement, switch_statement),
        (CaseStatement, case_statement), (DefaultStatement, case_statement),
    )
)