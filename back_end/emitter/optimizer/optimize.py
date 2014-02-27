__author__ = 'samyvilar'

from collections import defaultdict
from itertools import chain, imap, izip, repeat, ifilter

from utils.sequences import takewhile, peek, consume, __required__, exhaust, peek_or_terminal, terminal
from utils.rules import get_rule, set_rules
from utils.errors import error_if_not_type, raise_error
from back_end.emitter.object_file import Reference

from back_end.virtual_machine.instructions.architecture import Allocate, Pass, Operand
from back_end.virtual_machine.instructions.architecture import Instruction, referenced_obj, pop_instrs, operns, opern
from front_end.loader.locations import loc

new_instructions = {}  # keep track of the new instructions so new_instructions[id(old_instr)] = new_instr

new_references = {}

# TODO: bug, need to keep referencing previously deleted instructions!
# it seems pythons internal memory allocator may be reusing previously garbage collected objects
# which creates havoc for the optimizer since the id of the new object is reused
# and hence 'supposedly' new objects are in fact referenced old, applying update_instruction_references() fails ...
# removed_instrs = []
old_instructions = defaultdict(list)
# keep track of the removed instructions so old_instructions[id(new_instr)] = old_instrs

deleted_instructions = []


def replace_instr(old_instr, new_instr):
    if id(old_instr) == id(new_instr):  # instructions are identical do nothing ...
        return

    _ = id(old_instr) in new_instructions and raise_error(  # we are replacing an old instructions twice!!
        'We are replacing an old instruction {i} with {n} twice!'.format(i=old_instr, n=new_instr))

    if id(old_instr) in old_instructions:
        # we are replacing a previously new instruction ...
        # replacing new_instr so we need to replace previous references with this new_instr
        # instead of the old one ... get all the instructions that where referencing the older instruction ...
        previous_instructions = old_instructions[id(old_instr)]
        new_instructions.update(izip(imap(id, previous_instructions), repeat(new_instr)))  # update all previous
        old_instructions[id(new_instr)] = previous_instructions  # in case this new instruction should be updated again
        deleted_instructions.append(old_instr)
    else:
        new_instructions[id(old_instr)] = new_instr
        old_instructions[id(new_instr)].append(old_instr)  # a new instruction may replace more than 1 instruction.

    return new_instr


def replace_instrs(new_instr, old_instrs):
    return exhaust(imap(replace_instr, old_instrs, repeat(new_instr))) or new_instr


def remove_allocation(instrs):
    """
        optimize 1 or more sequence of allocations ...
        take their sum and if zero replace with the next instruction in case this one is referenced.
        other wise do one allocation and remove rest
        replace allocate 1 with POP, which only requires a single address translation vs 2 (instr, oprn) for allocate.
    """
    alloc_instrs = tuple(takewhile(lambda i: isinstance(i, Allocate) and isinstance(opern(i), (int, long)), instrs))

    if not alloc_instrs:  # Operand must be non-primitive type (Address) ... must wait for its value.
        yield consume(instrs)
    else:
        total = sum(imap(opern, alloc_instrs))

        if total:  # non-zero allocates changes the state of the stack.
            if total in pop_instrs:
                new_instr = next(pop_instrs[total](loc(alloc_instrs[0])))
            elif len(alloc_instrs) != 1:
                new_instr = alloc_instrs[0]
            else:
                new_instr = Allocate(loc(alloc_instrs[-1]), total)
            yield replace_instrs(new_instr, alloc_instrs)
        else:  # stack remains unchanged, get next instruction for referencing, it one exists ...
            if peek_or_terminal(instrs) is terminal:
                yield replace_instr(Pass(loc(alloc_instrs[-1])), alloc_instrs)
            else:
                replace_instrs(peek(instrs), alloc_instrs)


def remove_pass(instrs):
    """ replace 1 or more sequences of Pass by the next non-Pass instruction or Pass instruction  """
    pass_instrs = tuple(takewhile(lambda instr: isinstance(instr, Pass), instrs))
    if peek_or_terminal(instrs) is terminal:
        yield replace_instrs(pass_instrs[-1], pass_instrs[:-1])
    else:
        replace_instrs(peek(instrs), pass_instrs)


def get_new_instr(addr_operand, default):
    if isinstance(referenced_obj(addr_operand, None), Reference) and id(addr_operand) in new_references:
        # replace Reference by instruction
        default = addr_operand.obj = error_if_not_type(new_references[id(addr_operand)].obj, Reference)

    # if id(addr_operand.obj) not in new_instructions:
    #     print 'no address !!!', id(addr_operand.obj)
    # else:
    #     print id(addr_operand.obj), ' --> ', id(new_instructions[id(addr_operand.obj)])
    return new_instructions.get(id(addr_operand.obj), default)
    # _ = new_instr is __required__ and raise_error('No entry for instruction {i}'.format(i=addr_operand.obj))
    # return new_instr


def update_instruction_references(instrs):  # update operand references, since they may referencing omitted instructions
    references = []
    for instr in instrs:
        references.extend(ifilter(  # get all operands that are referencing something ...
            lambda o: isinstance(referenced_obj(o, None), (Operand, Reference, Instruction)), operns(instr, ())
        ))
        yield instr

    # for ref in references:
    #     new_obj = get_new_instr(ref, ref.obj)
    #     ref.obj = new_obj

    exhaust(imap(setattr, references, repeat('obj'), imap(get_new_instr, references, imap(referenced_obj, references))))
    # print 'done ...'
    # print '.\n'.join(imap(str, references))


def no_optimization(instrs):
    return consume(instrs),


zero_level_optimization = no_optimization


def first_level_optimization(instrs):
    return get_rule(first_level_optimization, peek(instrs), hash_funcs=(type,))(instrs)
set_rules(first_level_optimization, ((Allocate, remove_allocation), (Pass, remove_pass)), zero_level_optimization)


def optimize(instrs, level=zero_level_optimization):
    global new_instructions, old_instructions, deleted_instructions
    new_instructions = {}
    old_instructions = defaultdict(list)
    deleted_instructions = []
    return update_instruction_references(chain.from_iterable(imap(level, takewhile(peek, repeat(instrs)))))