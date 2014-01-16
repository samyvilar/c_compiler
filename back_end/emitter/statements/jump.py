__author__ = 'samyvilar'

from itertools import chain

from front_end.loader.locations import loc
from front_end.parser.ast.expressions import exp
from front_end.parser.ast.declarations import name
from front_end.parser.ast.statements import BreakStatement, ContinueStatement, ReturnStatement, GotoStatement
from front_end.parser.ast.statements import LabelStatement
from front_end.parser.types import c_type, void_pointer_type, VoidType, char_type

from back_end.virtual_machine.instructions.architecture import Pass, relative_jump, allocate, load_instr
from back_end.virtual_machine.instructions.architecture import Offset, load_base_stack_pointer, add, push, set_instr
from back_end.virtual_machine.instructions.architecture import Integer, absolute_jump, Allocate, RelativeJump, Address
from back_end.emitter.c_types import size

from back_end.emitter.expressions.expression import expression
from back_end.emitter.expressions.cast import cast


def break_statement(stmnt, symbol_table, stack, *_):
    try:
        instr, stack_pointer = symbol_table['__ break __']
    except KeyError as _:
        raise ValueError('{l} break statement outside loop/switch statement, could not calc jump addr'.format(
            l=loc(stmnt)
        ))
    return chain(
        update_stack(stack.stack_pointer, stack_pointer, loc(stmnt)),
        relative_jump(Offset(instr, loc(stmnt)), loc(stmnt))
    )


def continue_statement(stmnt, symbol_table, stack, *_):
    try:
        instr, stack_pointer = symbol_table['__ continue __']
    except KeyError as _:
        raise ValueError('{l} continue statement outside loop statement, could not calc jump addr'.format(
            l=loc(stmnt)
        ))
    return chain(
        update_stack(stack.stack_pointer, stack_pointer, loc(stmnt)),
        relative_jump(Offset(instr, loc(stmnt)), loc(stmnt))
    )


def return_instrs(location):
    return absolute_jump(
        load_instr(
            load_base_stack_pointer(location),
            size(void_pointer_type),
            location
        ),
        location
    )  # Jump back, caller is responsible for clean up as well as set up.


def return_statement(stmnt, symbol_table, *_):
    # TODO: check if we can omit the setting the return value if if it is immediately removed ...
    return_type = c_type(c_type(symbol_table['__ CURRENT FUNCTION __']))

    if isinstance(return_type, VoidType) or not exp(stmnt):
     # just return if void type or expr is empty or size of expression is zero.
        return return_instrs(loc(stmnt))

    return chain(
        cast(expression(exp(stmnt), symbol_table), c_type(exp(stmnt)), return_type, loc(stmnt)),
        set_instr(
            load_instr(
                add(load_base_stack_pointer(loc(stmnt)), push(size(void_pointer_type), loc(stmnt)), loc(stmnt)),
                size(void_pointer_type),
                loc(stmnt)
            ),
            size(return_type),
            loc(stmnt)
        ),
        # TODO: see if we can remove the following instr, since pop_frame will reset the base and stack pointers
        # allocate(-size(return_type), loc(stmnt)),  # Set leaves the value on the stack
        return_instrs(loc(stmnt))
    )


def update_stack(source_stack_pointer, target_stack_pointer, location):
    return allocate(source_stack_pointer - target_stack_pointer, location)


# goto is really trouble some, specially on stack based machines, since it can bypass definitions, corrupting offsets.
# The only way to deal with with it is to save the stack state on the labelled and goto instructions, and recreate the
# the appropriate stack state before Jumping.
def goto_statement(stmnt, symbol_table, stack, *_):
    labels, gotos = symbol_table['__ LABELS __'], symbol_table['__ GOTOS __']

    if stmnt.label in labels:  # Label previously defined either in current or previous scope ... nothing to do ...
        instr, stack_pointer = labels[stmnt.label]
        instrs = chain(
            update_stack(stack_pointer, stack.stack_pointer, loc(stmnt)),
            relative_jump(Offset(instr, loc(stmnt)), loc(stmnt))
        )
    else:
        # Label has yet to be defined ...
        # Basically we need to update the relative jump and the amount to which we need to update the stack ...
        # TODO: use a better approach, we can't use Address since it'll be translated ...
        alloc_instr = Allocate(loc(stmnt), Offset(Integer(0), loc(stmnt)))
        jump_instr = RelativeJump(loc(stmnt), Offset(None, loc(stmnt)))

        gotos[stmnt.label].append((alloc_instr, jump_instr, stack.stack_pointer))
        instrs = (alloc_instr, jump_instr)

    return instrs


def label_statement(stmnt, symbol_table, stack, statement_func):
    instr = Pass(loc(stmnt))

    labels, gotos = symbol_table['__ LABELS __'], symbol_table['__ GOTOS __']
    labels[name(stmnt)] = (instr, stack.stack_pointer)

    # update all previous gotos referring to this lbl
    for alloc_instr, rel_jump_instr, goto_stack_pointer in gotos[name(stmnt)]:
        # TODO: bug! set_address uses obj.address.
        alloc_instr[0].obj.address = alloc_instr.address + (stack.stack_pointer - goto_stack_pointer)

        rel_jump_instr[0].obj = instr
    del gotos[name(stmnt)][:]

    return chain((instr,), statement_func(stmnt.statement, symbol_table, stack))
label_statement.rules = {LabelStatement}


def jump_statement(stmnt, symbol_table, statement_func, stack):
    return jump_statement.rules[type(stmnt)](stmnt, symbol_table, statement_func, stack)
jump_statement.rules = {
    BreakStatement: break_statement,
    ContinueStatement: continue_statement,
    ReturnStatement: return_statement,
    GotoStatement: goto_statement,
}