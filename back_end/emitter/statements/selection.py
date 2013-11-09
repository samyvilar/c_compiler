__author__ = 'samyvilar'

from itertools import chain
from copy import deepcopy

from front_end.loader.locations import loc
from front_end.parser.symbol_table import push, pop
from front_end.parser.ast.expressions import exp
from front_end.parser.ast.statements import IfStatement, SwitchStatement, CaseStatement, DefaultStatement
from front_end.parser.types import CharType, ShortType, IntegerType, LongType, c_type

from back_end.emitter.expressions.expression import expression
from back_end.virtual_machine.instructions.architecture import Pass, Offset, jump_false, relative_jump, jump_table

from back_end.emitter.statements.jump import update_stack


def if_statement(stmnt, symbol_table, stack, statement_func):
    end_of_if, end_of_else = Pass(loc(stmnt)), Pass(loc(stmnt))

    # def else_statement(stmnt, symbol_table, stack, statement_func):
    #     for instr in statement_func(stmnt.else_statement.statement, symbol_table, stack):
    #         yield instr

    for instr in chain(
        jump_false(expression(exp(stmnt), symbol_table), Offset(end_of_if, loc(end_of_if)), loc(end_of_if)),
        statement_func(stmnt.statement, symbol_table, stack)
    ):
        yield instr

    else_stmnt = stmnt.else_statement.statement
    if else_stmnt:
        for instr in chain(
            relative_jump(Offset(end_of_else, loc(end_of_else)), loc(stmnt)),
            (end_of_if,),
            statement_func(else_stmnt, symbol_table, stack),
            (end_of_else,),
        ):
            yield instr
    else:
        yield end_of_if


def case_statement(stmnt, symbol_table, stack, statement_func):
    try:
        _ = symbol_table['__ switch __']
    except KeyError as _:
        raise ValueError('{l} case statement outside switch statement'.format(l=loc(stmnt)))
    initial_instr = Pass(loc(stmnt))
    stmnt.stack = deepcopy(stack)  # case statements may be placed in nested compound statements.
    initial_instr.case = stmnt
    return chain((initial_instr,), statement_func(stmnt.statement, symbol_table, stack))


def switch_statement(stmnt, symbol_table, stack, statement_func):
    end_switch = Pass(loc(stmnt))
    stmnt.stack = deepcopy(stack)

    # if switch inside loop, only update end_instruct, since continue jumps to start of loop break goes to end of switch
    def body(stmnt, symbol_table, stack, statement_func, end_switch):
        symbol_table = push(symbol_table)
        symbol_table['__ break __'] = (end_switch, stack.stack_pointer)
        symbol_table['__ switch __'] = True

        allocation_table = []  # create an allocation table to update stack before jump in case of nested definitions
        switch_body_instrs = []
        cases = {'default': Offset(end_switch, loc(stmnt))}

        for instr in statement_func(stmnt.statement, symbol_table, stack):
            if isinstance(getattr(instr, 'case', None), CaseStatement):
                start = Pass(loc(instr))
                allocation_table.append(
                    chain(
                        (start,),
                        update_stack(stmnt.stack.stack_pointer, instr.case.stack.stack_pointer, loc(instr)),
                        relative_jump(Offset(instr, loc(instr)), loc(instr)),
                    )
                )
                cases[
                    (isinstance(instr.case, DefaultStatement) and 'default') or exp(exp(instr.case))
                ] = Offset(start, loc(instr))
                del instr.case
            switch_body_instrs.append(instr)

        if isinstance(c_type(exp(stmnt)), CharType):
            max_switch_value = 2**8 - 1
        elif isinstance(c_type(exp(stmnt)), ShortType):
            max_switch_value = 2**16 - 1
        elif isinstance(c_type(exp(stmnt)), IntegerType):
            max_switch_value = 2**32 - 1
        elif isinstance(c_type(exp(stmnt)), LongType):
            max_switch_value = 2**64 - 1
        else:
            raise ValueError('{l} Expected an integral type got {g}'.format(g=c_type(exp(stmnt)), l=loc(stmnt)))

        # yield JumpTable(loc(stmnt), cases)
        # for instr in chain.from_iterable(allocation_table):
        #     yield instr
        for instr in jump_table(loc(stmnt), cases, allocation_table, max_switch_value, switch_body_instrs):
            yield instr
        _ = pop(symbol_table)

    return chain(
        expression(exp(stmnt), symbol_table),
        body(stmnt, symbol_table, stack, statement_func, end_switch),
        (end_switch,)
    )


def selection_statement(stmnt, symbol_table, stack, statement_func):
    return selection_statement.rules[type(stmnt)](stmnt, symbol_table, stack, statement_func)
selection_statement.rules = {
    IfStatement: if_statement,
    SwitchStatement: switch_statement,
    CaseStatement: case_statement,
    DefaultStatement: case_statement,
}