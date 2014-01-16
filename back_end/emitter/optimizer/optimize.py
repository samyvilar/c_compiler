__author__ = 'samyvilar'

import inspect

from collections import defaultdict
from itertools import chain, imap, izip, repeat, ifilter, starmap
from utils.sequences import takewhile, peek, consume, __required__
from back_end.emitter.object_file import Reference
import back_end.virtual_machine.instructions.architecture as Architecture
from back_end.virtual_machine.instructions.architecture import operns, opern, Allocate, Pass, Operand
from back_end.virtual_machine.instructions.architecture import Instruction, referenced_obj
from back_end.virtual_machine.instructions.architecture import Pop, Push, LoadRegister, Dup, copy_instruction as copy_i
from front_end.loader.locations import loc

new_instructions = {}
new_references = {}

# TODO: bug, need to keep referencing previously deleted instructions!
# it seems pythons internal memory allocator may be reusing previously garbage collected objects
# which creates havoc for the optimizer since the id of the new object is reused
# and hence 'supposedly' new objects are in fact referenced old, applying update_instruction_references() fails ...
removed_instrs = []


def replace_instr(old_instr, new_instr):
    if id(old_instr) == id(new_instr):
        return

    if id(old_instr) in new_instructions:  # we are replacing an old instructions twice
        raise ValueError('We are replacing an old instruction {i} with {n} twice!'.format(i=old_instr, n=new_instr))

    if id(old_instr) in set(imap(id, new_instructions.itervalues())):
        # replacing new_instruction again so we need to update previous references with
        # this new instruction instead of the old one ...
        # get all the instructions that where referencing the older instruction ...
        for orig, prev_new_instr in ifilter(
                lambda item: id(item[1]) == id(old_instr),
                new_instructions.iteritems()
        ):
            new_instructions[orig] = new_instr
        removed_instrs.append(old_instr)

    elif id(old_instr) != id(new_instr):
        new_instructions[id(old_instr)] = new_instr
        removed_instrs.append(old_instr)


def copy_instruction(current_instr):
    new_instr = copy_i(current_instr)

    # check if the new instruction is referencing a symbol ...
    for new_operand, old_operand in izip(
            ifilter(lambda o: isinstance(referenced_obj(o, None), Reference), operns(new_instr, ())),
            ifilter(lambda o: isinstance(referenced_obj(o, None), Reference), operns(current_instr, ()))
    ):
        if id(new_operand) != id(old_operand):
            new_references[id(new_operand)] = old_operand

    return new_instr


def get_new_instr(addr_operand, default=__required__):
    if isinstance(referenced_obj(addr_operand, None), Reference) and id(addr_operand) in new_references:
        # replace Reference by instruction
        default = addr_operand.obj = new_references[id(addr_operand)].obj
        assert not isinstance(new_references[id(addr_operand)].obj, Reference)

    new_instr = new_instructions.get(id(addr_operand.obj), default)
    if new_instr is __required__:
        raise ValueError('No entry for instruction {i}'.format(i=addr_operand.obj))
    return new_instr


def allocation(instrs):
    """
        optimize 1 or more sequence of allocations ...
        take their sum and if zero replace with the next instruction in case this one is referenced.
        other wise do one allocation and remove rest
        replace allocate 1 with POP, which only requires a single address translation vs 2 (instr, oprn) for allocate.
    """
    allocations = tuple(takewhile(
        lambda instr: isinstance(instr, Allocate) and isinstance(opern(instr), (int, long)),
        instrs
    ))

    if not allocations:  # Operand must be non-primitive type (Address) ... must wait for its value.
        yield consume(instrs)
    else:
        total = sum(imap(long, imap(opern, allocations)))

        if total:  # non-zero allocates changes the state of the stack.
            if len(allocations) == 1:  # if single allocation, replace with faster Pop if removing single value
                new_instr = Pop(loc(allocations[0])) if opern(allocations[0]) == 1 else allocations[0]
            else:
                new_instr = Allocate(loc(allocations[0]), total)
            for alloc_instr in allocations:
                replace_instr(alloc_instr, new_instr)
            yield new_instr
        else:  # stack remains unchanged, get next instruction for referencing.
            new_instr = peek(instrs)
            for alloc_instr in allocations:
                replace_instr(alloc_instr, new_instr)


def remove_pass(instrs):
    """
        replace 1 or more sequences of Pass by the next non-Pass instruction or Pass instruction
        if no more instructions ...
    """
    passes = tuple(takewhile(lambda instr: isinstance(instr, Pass), instrs))
    next_value = peek(instrs, None)
    new_instr = next_value if isinstance(next_value, Instruction) else Pass(loc(passes[0]))

    for pass_instr in passes:
        replace_instr(pass_instr, new_instr)

    if isinstance(new_instr, Pass):  # only yield if new Pass instruction had to be created.
        yield new_instr


def remove_dup(instrs):
    """
        replace (Push or LoadRegister), DUP 1 by (Push or LoadRegister), (Push or LoadRegister)
    """
    current_instr = consume(instrs)
    if peek(instrs, None) == Dup('', 1):
        new_instr = copy_instruction(current_instr)
        replace_instr(consume(instrs), new_instr)
        return current_instr, new_instr
    return current_instr,


no_optimization = lambda: lambda instrs: (consume(instrs),)
zero_level_optimizations = defaultdict(no_optimization)

first_level_optimizations = defaultdict(no_optimization)
first_level_optimizations.update(chain(
    (
        (Allocate, allocation),
        (Pass, remove_pass)
    ),
    izip(
        ifilter(  # Get all classes that load a value on to the stack ...
            lambda obj: inspect.isclass(obj) and issubclass(obj, (Push, LoadRegister)),
            starmap(getattr, izip(repeat(Architecture), dir(Architecture)))
        ),
        repeat(remove_dup)
    )
))


def update_instruction_references(instrs):
    references = []
    for instr in instrs:
        for index, operand in enumerate(operns(instr, ())):
            if isinstance(referenced_obj(operand, None), (Operand, Reference, Instruction)):
                references.append(operand)
        yield instr

    # all instructions have being emitted ...
    # At this point resolve() should have resolved everything, replace Address references, with new instructions.
    for ref in references:
        ref.obj = get_new_instr(ref, ref.obj)
        assert not isinstance(ref.obj, Reference)


def optimize(instrs, rules=zero_level_optimizations):
    def _peek(instrs):
        while True:
            yield peek(instrs)

    return update_instruction_references(
        chain.from_iterable(
            imap(lambda i: rules[type(i)](instrs), _peek(instrs))
        )
    )