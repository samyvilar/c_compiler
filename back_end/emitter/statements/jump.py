__author__ = 'samyvilar'

from itertools import chain

from front_end.loader.locations import loc
from front_end.parser.ast.expressions import exp
from front_end.parser.ast.declarations import name
from front_end.parser.ast.statements import BreakStatement, ContinueStatement, ReturnStatement, GotoStatement
from front_end.parser.ast.statements import LabelStatement
from front_end.parser.types import c_type, void_pointer_type, VoidType

from back_end.virtual_machine.instructions.architecture import Push, Address, AbsoluteJump, Pass, RelativeJump, allocate
from back_end.virtual_machine.instructions.architecture import LoadBaseStackPointer, Integer, Set, Load, Add, Subtract
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
        (RelativeJump(loc(stmnt), Address(instr, loc(stmnt))),)
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
        (RelativeJump(loc(stmnt), Address(instr, loc(stmnt))),)
    )


def return_instrs(location):
    yield LoadBaseStackPointer(location)
    yield Push(location, Address(1, location))
    yield Add(location)
    yield Load(location, size(void_pointer_type))  # Push return Address.
    yield AbsoluteJump(location)  # Jump back, caller is responsible for clean up as well as set up.


def return_statement(stmnt, symbol_table, *_):
    return_type = c_type(c_type(symbol_table['__ CURRENT FUNCTION __']))
    if isinstance(return_type, VoidType):
        return return_instrs(loc(stmnt))
    return chain(
        cast(expression(exp(stmnt), symbol_table), c_type(exp(stmnt)), return_type, loc(stmnt)),
        (  # Copy return value onto stack
            LoadBaseStackPointer(loc(stmnt)),
            # move to previous frame, skipping return address ...
            Push(loc(stmnt), Address(1 + size(void_pointer_type), loc(stmnt))),
            Add(loc(stmnt)),
            Load(loc(stmnt), size(void_pointer_type)),
            # copy return value to previous Frame.
            Set(loc(stmnt), size(return_type)),
        ),
        allocate(Integer(-size(return_type), loc(stmnt))),  # Set leaves the value on the stack
        return_instrs(loc(stmnt))
    )


def update_stack(source_stack_pointer, target_stack_pointer, location):
    return allocate(Address(source_stack_pointer - target_stack_pointer, location))


# goto is really trouble some, specially on stack based machines, since it can bypass definitions, corrupting offsets.
# The only way to deal with with it is to save the stack state on the labelled and goto instructions, and recreate the
# the appropriate stack state before Jumping.
def goto_statement(stmnt, symbol_table, stack, *_):
    labels, gotos = symbol_table['__ LABELS __'], symbol_table['__ GOTOS __']

    if stmnt.label in labels:  # Label previously defined either in current or previous scope ...
        instr, stack_pointer = labels[stmnt.label]
        instrs = chain(
            update_stack(stack_pointer, stack.stack_pointer, loc(stmnt)),
            (RelativeJump(loc(stmnt), Address(instr, loc(stmnt))),)
        )
    else:  # Label has yet to be defined ...
        _load_sp, _push, _add, _set_st = allocate(Address(None, loc(stmnt)))
        # Allocate negates the amount since it calls add
        # TODO, update allocate so it doesn't negate but calls slightly slower sub

        # Basically we need to update the relative jump and the amount to which we need to update the stack ...
        alloc_operand_addr = Address(None, loc(stmnt))
        jump_operand_addr = Address(None, loc(stmnt))
        gotos[stmnt.label].append((alloc_operand_addr, jump_operand_addr, stack.stack_pointer))
        instrs = (
            _load_sp,
            Push(loc(stmnt), alloc_operand_addr),
            Subtract(loc(stmnt)),
            _set_st,
            RelativeJump(loc(stmnt), jump_operand_addr)
        )

    return instrs


def label_statement(stmnt, symbol_table, stack, statement_func):
    instr = Pass(loc(stmnt))

    labels, gotos = symbol_table['__ LABELS __'], symbol_table['__ GOTOS __']
    labels[name(stmnt)] = (instr, stack.stack_pointer)

    # update all previous gotos referring to this lbl
    for alloc_operand_addr, rel_jump_addr, goto_stack_pointer in gotos[name(stmnt)]:
        # we invert since allocate negates the amount
        alloc_operand_addr.obj = Integer(goto_stack_pointer - stack.stack_pointer, loc(alloc_operand_addr))
        alloc_operand_addr.obj.address = alloc_operand_addr.obj  # TODO: bug! set_address uses obj.address.
        rel_jump_addr.obj = instr
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