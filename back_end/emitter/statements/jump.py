__author__ = 'samyvilar'

from itertools import chain, imap

from utils.rules import set_rules, rules

from front_end.loader.locations import loc
from front_end.parser.ast.expressions import exp
from front_end.parser.ast.declarations import name
from front_end.parser.ast.statements import BreakStatement, ContinueStatement, ReturnStatement, GotoStatement
from front_end.parser.ast.statements import LabelStatement
from front_end.parser.types import c_type, void_pointer_type, VoidType, char_type, ArrayType

from back_end.virtual_machine.instructions.architecture import Pass, relative_jump, allocate, load
from back_end.virtual_machine.instructions.architecture import Offset, load_base_stack_pointer, add, push, set_instr
from back_end.virtual_machine.instructions.architecture import Integer, absolute_jump, Allocate, RelativeJump, Address
from back_end.emitter.c_types import size

from back_end.emitter.expressions.cast import cast


def break_statement(stmnt, symbol_table):
    try:
        instr, stack_pointer = symbol_table['__ break __']
    except KeyError as _:
        raise ValueError('{l} break statement outside loop/switch statement, could not calc jump addr'.format(
            l=loc(stmnt)
        ))
    return chain(
        update_stack(symbol_table['__ stack __'].stack_pointer, stack_pointer, loc(stmnt)),
        relative_jump(Offset(instr, loc(stmnt)), loc(stmnt))
    )


def continue_statement(stmnt, symbol_table):
    try:
        instr, stack_pointer = symbol_table['__ continue __']
    except KeyError as _:
        raise ValueError('{l} continue statement outside loop statement, could not calc jump addr'.format(
            l=loc(stmnt)
        ))
    return chain(
        update_stack(symbol_table['__ stack __'].stack_pointer, stack_pointer, loc(stmnt)),
        relative_jump(Offset(instr, loc(stmnt)), loc(stmnt))
    )


def return_instrs(location):  # Jump back, caller is responsible for cleaning up as well as set up.
    return absolute_jump(load(load_base_stack_pointer(location), size(void_pointer_type), location), location)


def return_statement(stmnt, symbol_table):
    # TODO: check if we can omit the setting the return value if if it is immediately removed ...
    return_type = c_type(c_type(symbol_table['__ CURRENT FUNCTION __']))
    assert not isinstance(c_type(return_type), ArrayType)
    if isinstance(return_type, VoidType) or not exp(stmnt):
     # just return if void type or expr is empty or size of expression is zero.
        return return_instrs(loc(stmnt))

    return chain(
        cast(symbol_table['__ expression __'](exp(stmnt), symbol_table), c_type(exp(stmnt)), return_type, loc(stmnt)),
        set_instr(
            load(
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
def goto_statement(stmnt, symbol_table):
    labels, gotos, stack = imap(symbol_table.__getitem__, ('__ LABELS __', '__ GOTOS __', '__ stack __'))

    if stmnt.label in labels:  # Label previously defined either in current or previous scope ... nothing to do ...
        instr, stack_pointer = labels[stmnt.label]
        instrs = chain(
            update_stack(stack_pointer, stack.stack_pointer, loc(stmnt)),
            relative_jump(Offset(instr, loc(stmnt)), loc(stmnt))
        )
    else:
        # Label has yet to be defined ...
        # Basically we need to update the relative jump and the amount to which we need to update the stack ...
        # TODO: find/use a better approach, we can't use Address since it'll be translated ...
        alloc_instr = Allocate(loc(stmnt), Offset(Integer(0), loc(stmnt)))
        jump_instr = RelativeJump(loc(stmnt), Offset(None, loc(stmnt)))

        gotos[stmnt.label].append((alloc_instr, jump_instr, stack.stack_pointer))
        instrs = (alloc_instr, jump_instr)

    return instrs


def label_statement(stmnt, symbol_table):
    instr = Pass(loc(stmnt))
    labels, gotos, stack, statement = imap(
        symbol_table.__getitem__, ('__ LABELS __', '__ GOTOS __', '__ stack __', '__ statement __')
    )
    labels[name(stmnt)] = (instr, symbol_table['__ stack __'].stack_pointer)

    # update all previous gotos referring to this lbl
    for alloc_instr, rel_jump_instr, goto_stack_pointer in gotos[name(stmnt)]:
        # TODO: bug! set_address uses obj.address.
        alloc_instr[0].obj.address = alloc_instr.address + (stack.stack_pointer - goto_stack_pointer)
        rel_jump_instr[0].obj = instr

    del gotos[name(stmnt)][:]
    return chain((instr,), statement(stmnt.statement, symbol_table))
set_rules(label_statement, {LabelStatement})


def jump_statement(stmnt, symbol_table):
    return rules(jump_statement)[type(stmnt)](stmnt, symbol_table)
set_rules(
    jump_statement,
    (
        (BreakStatement, break_statement), (ContinueStatement, continue_statement),
        (ReturnStatement, return_statement), (GotoStatement, goto_statement),
    )
)