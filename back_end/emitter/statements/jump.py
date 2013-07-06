__author__ = 'samyvilar'

from copy import deepcopy
from itertools import chain

from front_end.loader.locations import loc
from front_end.parser.ast.expressions import exp
from front_end.parser.ast.statements import BreakStatement, ContinueStatement, ReturnStatement, GotoStatement
from front_end.parser.types import c_type

from back_end.virtual_machine.instructions.architecture import RestoreStackPointer, Push, Address, AbsoluteJump, JumpTrue
from back_end.virtual_machine.instructions.architecture import LoadBaseStackPointer, Integer, Set, Load, Add, Allocate, Pass
from back_end.virtual_machine.instructions.architecture import SaveStackPointer
from back_end.emitter.types import size

from back_end.emitter.expressions.expression import expression
from back_end.emitter.expressions.cast import cast


def relative_jump_instrs(address):
    yield Push(loc(address), Integer(1, loc(address)))
    yield JumpTrue(loc(address), address)


def break_statement(stmnt, symbol_table, stack, statement_func, jump_props):
    if not jump_props:
        raise ValueError('{l} break statement outside loop/switch statement, could not calc jump addr'.format(
            l=loc(stmnt)
        ))
    number_of_pops = len(stack) - jump_props[2]
    assert number_of_pops >= 0
    return chain(
        (RestoreStackPointer(loc(stmnt)) for _ in xrange(number_of_pops)),
        relative_jump_instrs(Address(jump_props[1], loc(stmnt)))
    )


def continue_statement(stmnt, symbol_table, stack, statement_func, jump_props):
    if not jump_props:
        raise ValueError('{l} continue statement outside loop/switch statement, could not calc jump addr'.format(
            l=loc(stmnt)
        ))
    number_of_pops = len(stack) - jump_props[2]
    assert number_of_pops >= 0
    return chain(
        (RestoreStackPointer(loc(stmnt)) for _ in xrange(number_of_pops)),
        relative_jump_instrs(Address(jump_props[0], loc(stmnt)))
    )


def return_instrs(location):
        yield LoadBaseStackPointer(location)
        yield Load(location, size(Address()))  # Push return Address.
        yield AbsoluteJump(location)  # Jump back, caller is responsible for clean up as well as set up.


def return_statement(stmnt, symbol_table, statement_func, stack, jump_props):
    return_type = c_type(c_type(symbol_table['__ CURRENT FUNCTION __']))
    return chain(
        cast(expression(exp(stmnt), symbol_table), c_type(exp(stmnt)), return_type, loc(stmnt)),
        (  # Copy return value onto stack
            LoadBaseStackPointer(loc(stmnt)),
            Push(loc(stmnt), Integer(1, loc(stmnt))),
            Add(loc(stmnt)),
            Set(loc(stmnt), size(return_type)),  # copy return value to previous Frame.
            Allocate(loc(stmnt), Integer(-1 * size(return_type), loc(stmnt))),  # Set leaves the value on the stack
        ),
        return_instrs(loc(stmnt))
    )


def patch_goto_instrs(goto_stmnt, label_stmnt):
    source_state, target_state = goto_stmnt.stack, label_stmnt.stack
    instrs, level = [], len(target_state) - len(source_state)

    if level > 0:  # Jumping into a nested compound statement.
        previous_stack_pointer = source_state.stack_pointer
        for stack_pointer in target_state[len(source_state):]:
            assert stack_pointer - previous_stack_pointer <= 0
            instrs.extend((
                Allocate(loc(goto_stmnt), Integer(previous_stack_pointer - stack_pointer, loc(goto_stmnt))),
                SaveStackPointer(loc(goto_stmnt)),
            ))
            previous_stack_pointer = stack_pointer
    else:
        if level < 0:  # Jumping out of a nested compound statement.
            instrs.extend(RestoreStackPointer(loc(goto_stmnt)) for _ in xrange(abs(level)))
            instrs.append(
                Allocate(
                    loc(goto_stmnt),
                    Integer(source_state[len(target_state)] - target_state.stack_pointer, loc(goto_stmnt)),
                )
            )
        else:
            instrs.append(
                Allocate(
                    loc(goto_stmnt),
                    Integer(source_state.stack_pointer - target_state.stack_pointer, loc(goto_stmnt))
                )
            )
    return instrs


# goto is really trouble some, specially on stack based machines, since it can by pass definitions, corrupting offsets.
# The only way to deal with with it is to save the stack state on the labelled instruction and goto, and recreate it
# before Jumping to it.
# Native goto binaries can only be generated once all the binaries of the function have being created.
def goto_statement(stmnt, symbol_table, stack, statement_func, jump_props):
    stmnt.stack = deepcopy(stack)  # Attach copy of state to goto TODO: find better method then deepcopy
    stmnt.instr = [Pass(loc(stmnt))]  # Set reference to jump Instruction.
    return stmnt.instr


def jump_statement(stmnt, symbol_table, statement_func, stack, jump_props):
    return jump_statement.rules[type(stmnt)](stmnt, symbol_table, statement_func, stack, jump_props)
jump_statement.rules = {
    BreakStatement: break_statement,
    ContinueStatement: continue_statement,
    ReturnStatement: return_statement,
    GotoStatement: goto_statement,
}