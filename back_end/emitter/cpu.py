__author__ = 'samyvilar'

import sys

from itertools import takewhile, imap, izip

from logging_config import logging

from front_end.loader.locations import loc, LocationNotSet

from back_end.emitter.c_types import size
from front_end.parser.types import IntegerType, void_pointer_type, CharType, PointerType, c_type, LongType
from back_end.emitter.object_file import Reference, Code, Data

from back_end.virtual_machine.instructions.architecture import Instruction, Allocate, Push, Pop, Halt, Pass, operns, Dup
from back_end.virtual_machine.instructions.architecture import Add, Subtract, Multiply, Divide, Mod
from back_end.virtual_machine.instructions.architecture import AddFloat, SubtractFloat, MultiplyFloat, DivideFloat
from back_end.virtual_machine.instructions.architecture import And, Or, Xor, Not, ShiftLeft, ShiftRight
from back_end.virtual_machine.instructions.architecture import ConvertToInteger, ConvertToFloat
from back_end.virtual_machine.instructions.architecture import LoadZeroFlag, LoadOverflowFlag, LoadCarryBorrowFlag
from back_end.virtual_machine.instructions.architecture import Jump, AbsoluteJump, CompoundSet
from back_end.virtual_machine.instructions.architecture import RelativeJump, JumpTrue, JumpFalse, JumpTable
from back_end.virtual_machine.instructions.architecture import LoadBaseStackPointer, LoadStackPointer, Load, Set
from back_end.virtual_machine.instructions.architecture import PushFrame, PopFrame, Enqueue, Dequeue, Address, Byte
from back_end.virtual_machine.instructions.architecture import Integer, SetBaseStackPointer


logger = logging.getLogger('virtual_machine')


def pop(cpu, mem):
    cpu.stack_pointer += 1
    return mem[cpu.stack_pointer]


def push(value, cpu, mem):
    assert isinstance(value, (int, float))
    mem[cpu.stack_pointer] = value
    cpu.stack_pointer -= 1


def add(oper1, oper2):
    return oper1 + oper2


def sub(oper1, oper2):
    return oper1 - oper2


def mult(oper1, oper2):
    return oper1 * oper2


def div(oper1, oper2):
    return oper1 / oper2


def _and(oper1, oper2):
    return oper1 & oper2


def _or(oper1, oper2):
    return oper1 | oper2


def _xor(oper1, oper2):
    return oper1 ^ oper2


def mod(oper1, oper2):
    return oper1 % oper2


def _shift_left(oper1, oper2):
    return oper1 << (oper2 & 0b111111)


def _shift_right(oper1, oper2):
    return oper1 >> oper2


def _not(oper1):
    return ~oper1


def convert_to_int(oper1):
    return int(oper1)


def convert_to_float(oper1):
    return float(oper1)


def bin_arithmetic(instr, cpu, mem):
    oper2, oper1 = pop(cpu, mem), pop(cpu, mem)
     # make sure emitter doesn't generate instr that mixes types.
    assert isinstance(oper1, int) and isinstance(oper2, int) or isinstance(oper1, float) and isinstance(oper2, float)
    result = bin_arithmetic.rules[type(instr)](oper1, oper2)
    if isinstance(instr, (Add, AddFloat, Subtract, SubtractFloat, Multiply, MultiplyFloat, Divide, DivideFloat)):
        cpu.overflow = cpu.carry = int(result < 0)
        cpu.zero = int(not result)
    return result
bin_arithmetic.rules = {
    Add: add,
    AddFloat: add,
    Subtract: sub,
    SubtractFloat: sub,
    Multiply: mult,
    MultiplyFloat: mult,
    Divide: div,
    DivideFloat: div,
    And: _and,
    Or: _or,
    Xor: _xor,
    Mod: mod,
    ShiftLeft: _shift_left,
    ShiftRight: _shift_right,
}


def unary_arithmetic(instr, cpu, mem):
    return unary_arithmetic.rules[type(instr)](pop(cpu, mem))
unary_arithmetic.rules = {
    Not: _not,
    ConvertToFloat: convert_to_float,
    ConvertToInteger: convert_to_int,
}


def expr(instr, cpu, mem):
    push(expr.rules[type(instr)](instr, cpu, mem), cpu, mem)
expr.rules = {rule: bin_arithmetic for rule in bin_arithmetic.rules}
expr.rules.update({rule: unary_arithmetic for rule in unary_arithmetic.rules})


def _jump(addr, cpu, mem):
    cpu.instr_pointer = addr


def abs_jump(instr, cpu, mem):
    _jump(pop(cpu, mem), cpu, mem)


def rel_jump(instr, cpu, mem):
    _jump(cpu.instr_pointer + operns(instr)[0], cpu, mem)


def jump_if_true(instr, cpu, mem):
    value = pop(cpu, mem)
    if value:
        _jump(cpu.instr_pointer + operns(instr)[0], cpu, mem)
    else:
        _pass(instr, cpu, mem)


def jump_if_false(instr, cpu, mem):
    value = pop(cpu, mem)
    if not value:
        _jump(cpu.instr_pointer + operns(instr)[0], cpu, mem)
    else:
        _pass(instr, cpu, mem)


def jump_table(instr, cpu, mem):
    _jump(instr.cases.get(pop(cpu, mem), instr.cases['default']).obj.address, cpu, mem)


def jump(instr, cpu, mem):
    jump.rules[type(instr)](instr, cpu, mem)
jump.rules = {
    RelativeJump: rel_jump,
    AbsoluteJump: abs_jump,
    JumpTrue: jump_if_true,
    JumpFalse: jump_if_false,
    JumpTable: jump_table,
}


def allocate(instr, cpu, mem):
    cpu.stack_pointer -= operns(instr)[0]


def _pass(instr, cpu, mem):
    cpu.instr_pointer += 1


def _dup(instr, cpu, mem):
    value = pop(cpu, mem)
    push(value, cpu, mem)
    push(value, cpu, mem)


def load_base_pointer(instr, cpu, mem):
    push(cpu.base_pointer, cpu, mem)


def set_base_pointer(instr, cpu, mem):
    cpu.base_pointer = _pop(instr, cpu, mem)


def load_stack_pointer(instr, cpu, mem):
    push(cpu.stack_pointer, cpu, mem)


def _load(instr, cpu, mem):
    addr, quantity = pop(cpu, mem), operns(instr)[0]
    for addr in reversed(xrange(addr, addr + quantity)):
        push(mem[addr], cpu, mem)


def stepper(initial_value=0, step=1):
    while True:
        yield initial_value
        initial_value += step


def _set(instr, cpu, mem):
    addr, quantity, stack_pointer = _pop(instr, cpu, mem), operns(instr)[0], cpu.stack_pointer + 1
    for addr, stack_addr in izip(xrange(addr, addr + quantity), xrange(stack_pointer, stack_pointer + quantity)):
        mem[addr] = mem[stack_addr]


def _compound_set(instr, cpu, mem):
    quantity = operns(instr)[0]
    for addr, value in enumerate(reversed([pop(cpu, mem) for _ in xrange(quantity)]), _pop(instr, cpu, mem)):
        push(value, cpu, mem)
        mem[addr] = value


def _push(instr, cpu, mem):
    push(operns(instr)[0], cpu, mem)


def _pop(instr, cpu, mem):
    return pop(cpu, mem)


def push_frame(instr, cpu, mem):
    cpu.frames.append((cpu.base_pointer, cpu.stack_pointer))


def create_frame(instr, cpu, mem):
    cpu.base_pointer = cpu.frames[-1][1]


def pop_frame(instr, cpu, mem):
    cpu.base_pointer, cpu.stack_pointer = cpu.frames.pop()


def enqueue(instr, cpu, mem):
    value = _pop(instr, cpu, mem)
    cpu.queue.append(value)
    push(value, cpu, mem)


def dequeue(instr, cpu, mem):
    push(cpu.queue.pop(0), cpu, mem)


def evaluate(cpu, mem, os=None):
    os = os or Kernel()
    while True:
        while cpu.instr_pointer in os.calls:
            os.calls[cpu.instr_pointer](cpu, mem, os)

        instr = mem[cpu.instr_pointer]
        if isinstance(instr, Halt):
            break
        evaluate.rules[type(instr)](instr, cpu, mem)
        if not isinstance(instr, (Pass, Jump)):  # do not update instr pointer, this instrs manipulate it.
            _pass(instr, cpu, mem)
evaluate.rules = {
    Pass: _pass,
    Push: _push,
    Pop: _pop,
    Dup: _dup,
    Allocate: allocate,
    LoadZeroFlag: lambda instr, cpu, mem: push(cpu.zero, cpu, mem),
    LoadCarryBorrowFlag: lambda instr, cpu, mem: push(cpu.carry, cpu, mem),
    LoadOverflowFlag: lambda instr, cpu, mem: push(cpu.overflow, cpu, mem),

    LoadBaseStackPointer: load_base_pointer,
    SetBaseStackPointer: set_base_pointer,
    LoadStackPointer: load_stack_pointer,

    PushFrame: push_frame,
    PopFrame: pop_frame,

    Enqueue: enqueue,
    Dequeue: dequeue,

    Load: _load,
    Set: _set,
    CompoundSet: _compound_set,
}
evaluate.rules.update({rule: expr for rule in expr.rules})
evaluate.rules.update({rule: jump for rule in jump.rules})


class Kernel(object):
    def __init__(self, calls=None):
        try:
            self.opened_files = {
                sys.stdin.fileno(): sys.stdin, sys.stdout.fileno(): sys.stdout, sys.stderr.fileno(): sys.stderr
            }
        except AttributeError as _:
            self.opened_files = {
                0: sys.stdin, 1: sys.stdout, 2: sys.stderr
            }
        self.calls = calls or {}


class CPU(object):
    def __init__(self):
        self.frames, self.queue = [], []
        self.instr_pointer = 1024
        self.zero, self.carry, self.overflow = 0, 0, 0
        self._stack_pointer, self.base_pointer = -1, -1

    @property
    def stack_pointer(self):
        return self._stack_pointer

    @stack_pointer.setter
    def stack_pointer(self, value):
        self._stack_pointer = value
        if self._stack_pointer > 0:
            assert False
        if self.stack_pointer > self.base_pointer:
            assert False


def address(curr=1024, step=1):  # Address 0 is the NULL Pointer.
    while True:
        yield curr
        curr += step


def load(instrs, mem, symbol_table=None, address_gen=None):
    address_gen = iter(address_gen or address())
    symbol_table = symbol_table or {}

    references = {}
    for instr in instrs:
        instr.address = next(address_gen)
        mem[instr.address] = instr
        if any(isinstance(o, Address) for o in operns(instr)):
            references[instr.address] = instr

    for addr, instr in references.iteritems():
        operands = []
        for o in operns(instr):
            obj = getattr(o, 'obj', None)
            if hasattr(obj, 'address'):
                ref_addr = o.obj.address
            elif isinstance(obj, Reference):
                symbol = symbol_table[o.obj.name]
                if hasattr(symbol, 'first_element'):
                    ref_addr = symbol.first_element.address
                else:
                    ref_addr = next(address_gen)
                    symbol.first_element = Byte(0, '')
                    symbol.first_element.address = ref_addr
                    mem[symbol.first_element.address] = symbol.first_element
                    mem.update({next(address_gen): Byte(0, '') for _ in xrange(symbol.size - 1)})
            else:
                ref_addr = o
            operands.append(ref_addr - (addr if isinstance(instr, RelativeJump) else 0))
        instr.operands = operands


__str__ = lambda ptr, mem, max_l=512: ''.join(imap(chr, takewhile(lambda byte: byte, __buffer__(ptr, max_l, mem))))
__buffer__ = lambda ptr, count, mem: (mem[ptr] for ptr in xrange(ptr, ptr + count))


from back_end.emitter.statements.jump import return_statement
from front_end.parser.ast.declarations import AbstractDeclarator
from front_end.parser.ast.statements import ReturnStatement
from front_end.parser.ast.expressions import ConstantExpression
from front_end.parser.types import FunctionType


def __return__(value, cpu, mem):
    location = '__ SYS_CALL __'
    instrs = return_statement(
        ReturnStatement(ConstantExpression(value, IntegerType(location), location), location),
        {'__ CURRENT FUNCTION __': FunctionType(IntegerType(location), (), location)}
    )
    for instr in instrs:
        evaluate.rules[type(instr)](instr, cpu, mem)


def argument_address(func_type, cpu, mem):
    index = 1 + 2 * size(void_pointer_type)
    for ctype in imap(c_type, func_type):
        yield cpu.base_pointer + index
        index += size(ctype)


def args(func_type, cpu, mem):
    for address, arg in izip(argument_address(func_type, cpu, mem), func_type):
        if size(c_type(arg)) == 1:
            yield mem[address]
        else:
            yield (mem[offset] for offset in xrange(address, address + size(arg)))


def __open__(cpu, mem, kernel):
    # int __open__(const char * file_path, const char *mode);  // returns file_id on success or -1 of failure.
    l = '__ SYS_CALL __'
    values = args(
        FunctionType(
            IntegerType(l),
            (AbstractDeclarator(PointerType(CharType(l), l), l), AbstractDeclarator(PointerType(CharType(l), l), l), ),
            l
        ),
        cpu,
        mem
    )

    file_id = Integer(-1, LocationNotSet)
    file_path_ptr, file_mode_ptr = values
    file_mode = __str__(file_mode_ptr, mem)
    if file_path_ptr in {sys.stdin.fileno(), sys.stdout.fileno(), sys.stderr.fileno()}:
        file_id = file_path_ptr
    else:
        file_name = __str__(file_path_ptr, mem)
        try:
            file_obj = open(file_name, file_mode)
            file_id = file_obj.fileno()
            kernel.opened_files[file_id] = file_obj
        except Exception as ex:
            logger.warning('failed to open file {f}, error: {m}'.format(f=file_name, m=ex))
    __return__(file_id, cpu, mem)


def __close__(cpu, mem, kernel):
    # int __close__(int);  // returns 0 on success or -1 on failure
    # // returns 0 on success or -1 on failure.
    l = '__ SYS_CALL __'
    values = args(
        FunctionType(
            IntegerType(l),
            (AbstractDeclarator(IntegerType(l), l),),
            l
        ),
        cpu,
        mem
    )

    file_id = next(values)
    return_value = Integer(-1, '__ SYS_CALL __')

    try:
        if file_id not in {sys.stdout.fileno(), sys.stdin.fileno(), sys.stderr.fileno()}:
            file_obj = kernel.opened_files.pop(file_id)
            file_obj.close()
        return_value = Integer(0, '__ SYS_CALL __')
    except KeyError as _:
        logger.warning('trying to close a non-opened file_id {f}'.format(f=file_id))
    except Exception as ex:
        logger.warning('failed to close file {f}, error: {m}'.format(f=file_obj.name, m=ex))
    __return__(return_value, cpu, mem)


def __read__(cpu, mem, kernel):
    # int __read__(int file_id, char *dest, unsigned long long number_of_bytes);
    # // returns the number of elements read on success or -1 on failure
    l = '__ SYS_CALL __'
    values = args(
        FunctionType(
            IntegerType(l),
            (
                AbstractDeclarator(IntegerType(l), l),
                AbstractDeclarator(PointerType(CharType(l), l), l),
                AbstractDeclarator(LongType(LongType(IntegerType(l), l, unsigned=True), l), l)
            ),
            l
        ),
        cpu,
        mem,
    )

    file_id, dest_ptr, number_of_bytes = values
    return_value = Integer(-1, LocationNotSet)

    try:
        file_id = kernel.opened_files[file_id]
        values = file_id.read(number_of_bytes)
        for addr, value in izip(xrange(dest_ptr, dest_ptr + len(values)), imap(ord, values)):
            mem[addr] = Byte(value, LocationNotSet)
        return_value = Integer(len(values), LocationNotSet)
    except KeyError as _:
        logger.warning('trying to read from a non-opened file_id {f}'.format(f=file_id))
    except Exception as ex:
        logger.warning('failed to read from file {f}, error: {m}'.format(f=getattr(file_id, 'name', file_id), m=ex))
    __return__(return_value, cpu, mem)


def __write__(cpu, mem, kernel):
    # int  __write__(int file_id, char *buffer, unsigned long long number_of_bytes);
    # // returns 0 on success or -1 on failure.
    l = '__ SYS_CALL __'
    values = args(
        FunctionType(
            IntegerType(l),
            (
                AbstractDeclarator(IntegerType(l), l),
                AbstractDeclarator(PointerType(CharType(l), l), l),
                AbstractDeclarator(LongType(LongType(IntegerType(l), l), l, unsigned=True), l)
            ),
            l
        ),
        cpu,
        mem
    )

    file_id, buffer_ptr, number_of_bytes = values
    return_value = Integer(-1, LocationNotSet)

    values = ''.join(imap(chr, __buffer__(buffer_ptr, number_of_bytes, mem)))
    try:
        file_id = kernel.opened_files[file_id]
        file_id.write(values)
        return_value = Integer(0, LocationNotSet)
    except KeyError as _:
        logger.warning('trying to write to a non-opened file_id {f}'.format(f=file_id))
    except Exception as ex:
        logger.warning('failed to write to file {f}, error: {m}'.format(f=getattr(file_id, 'name', file_id), m=ex))
        return_value = Integer(-1, LocationNotSet)
    __return__(return_value, cpu, mem)


def __tell__(cpu, mem, kernel):
    # int __tell__(int);
    l = '__ SYS_CALL __'
    values = args(
        FunctionType(IntegerType(l), (AbstractDeclarator(IntegerType(l), l),), l),
        cpu,
        mem
    )
    return_value = Integer(-1, LocationNotSet)
    file_id, = values

    try:
        file_id = kernel.opened_files[file_id]
        return_value = Integer(file_id.tell(), LocationNotSet)
    except KeyError as _:
        logger.warning('trying to ftell on a non-opened file_id {f}'.format(f=file_id))
    except Exception as ex:
        logger.warning('failed to ftell on file {f}, error: {m}'.format(f=getattr(file_id, 'name', file_id), m=ex))
    __return__(return_value, cpu, mem)


def __seek__(cpu, mem, kernel):
    # int __seek__(int file_id, int offset, int whence);
    l = '__ SYS_CALL __'
    values = args(
        FunctionType(
            IntegerType(l),
            (
                AbstractDeclarator(IntegerType(l), l),
                AbstractDeclarator(IntegerType(l), l),
                AbstractDeclarator(IntegerType(l), l),
            ),
            l
        ),
        cpu,
        mem
    )

    file_id, offset, whence = values
    return_value = Integer(-1, LocationNotSet)
    try:
        file_id = kernel.opened_files[file_id]
        file_id.seek(offset, whence)
        return_value = Integer(0, LocationNotSet)
    except KeyError as _:
        logger.warning('trying to fseek on non-opened file_id {f}'.format(f=file_id))
    except Exception as ex:
        logger.warning('failed to fseek on file {f}, error: {m}'.format(f=getattr(file_id, 'name', file_id), m=ex))
    __return__(return_value, cpu, mem)


def foo():
    raise Exception('')


class PassImmutable(object):
    def __init__(self, addr):
        self.addr = addr

    @property
    def address(self):
        return self.addr

    @address.setter
    def address(self, _):
        pass


class SystemCall(Code):
    def __init__(self, name, size, storage_class, location, call_id):
        self._first_element = PassImmutable(call_id)
        super(SystemCall, self).__init__(name, (Pass(LocationNotSet),), size, storage_class, location)

    @property
    def first_element(self):
        return self._first_element

    @first_element.setter
    def first_element(self, _):
        pass

SYMBOLS = {}
CALLS = {}
for call_name, call_id, call_code in (
    ('__open__', 5, __open__),
    ('__read__', 3, __read__),
    ('__write__', 4, __write__),
    ('__close__', 6, __close__),
    ('__tell__', 198, __tell__),
    ('__seek__', 199, __seek__),
):
    SYMBOLS[call_name] = SystemCall(call_name, 1, None, LocationNotSet, call_id)
    CALLS[call_id] = call_code