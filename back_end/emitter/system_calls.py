from back_end.emitter.object_file import Code

__author__ = 'samyvilar'

from itertools import imap, takewhile, izip, ifilter
from front_end.loader.locations import Location, LocationNotSet
from front_end.parser.types import IntegerType, VoidType, FunctionType, void_pointer_type, c_type, PointerType, CharType
from front_end.parser.types import LongType

from front_end.parser.ast.declarations import AbstractDeclarator

from back_end.emitter.c_types import size
from back_end.virtual_machine.instructions.architecture import Integer, Byte, Push
from back_end.virtual_machine.instructions.architecture import SystemCall as SysCallInstruction, push_integral

from back_end.emitter.cpu import std_files, logger, Halt, word_size
from back_end.emitter.c_types import function_operand_type_sizes

__str__ = lambda ptr, mem, max_l=512: ''.join(imap(chr, takewhile(lambda byte: byte, __buffer__(ptr, max_l, mem))))
__buffer__ = lambda ptr, count, mem: imap(mem.__getitem__, xrange(ptr, ptr + (count * word_size), word_size))


SysCallLocation = Location('__ SYS_CALL __', '', '')


def __return__(value, cpu, mem, os, func_signature=FunctionType(IntegerType(SysCallLocation), (), SysCallLocation)):
    cpu.instr_pointer = mem[cpu.base_pointer + word_size]  # get return instruction ...
    assert size(c_type(c_type(func_signature))) == word_size
    mem[cpu.base_pointer + 2 * word_size] = value


def argument_address(func_type, cpu, mem):
    index = 2 * size(void_pointer_type) + (
        size(void_pointer_type) if function_operand_type_sizes(c_type(c_type(func_type))) else 0
    )

    for ctype in imap(c_type, func_type):
        yield cpu.base_pointer + index
        index += size(ctype)


def args(func_type, cpu, mem):
    for address, arg in izip(argument_address(func_type, cpu, mem), func_type):
        yield mem[address] \
            if size(c_type(arg)) == word_size \
            else (mem[offset] for offset in xrange(address, address + size(c_type(arg)), word_size))


def __open__(
        cpu,
        mem,
        kernel,
        func_signature=FunctionType(
            IntegerType(SysCallLocation),
            (
                AbstractDeclarator(PointerType(CharType(SysCallLocation), SysCallLocation), SysCallLocation),
                AbstractDeclarator(PointerType(CharType(SysCallLocation), SysCallLocation), SysCallLocation),
            ),
            SysCallLocation
        )):
    # int __open__(const char * file_path, const char *mode);  // returns file_id on success or -1 of failure.
    values = args(func_signature, cpu, mem)

    file_id = Integer(-1, LocationNotSet)
    file_path_ptr, file_mode_ptr = values
    file_mode = __str__(file_mode_ptr, mem)
    if file_path_ptr in std_files:
        file_id = file_path_ptr
    else:
        file_name = __str__(file_path_ptr, mem)
        try:
            file_obj = open(file_name, file_mode)
            file_id = file_obj.fileno()
            kernel.opened_files[file_id] = file_obj
        except Exception as ex:
            logger.warning('failed to open file {f}, error: {m}'.format(f=file_name, m=ex))
    __return__(file_id, cpu, mem, kernel)


def __close__(
        cpu,
        mem,
        kernel,
        func_signature=FunctionType(
            IntegerType(SysCallLocation),
            (AbstractDeclarator(IntegerType(SysCallLocation), SysCallLocation),),
            SysCallLocation
        )):
    # int __close__(int);  // returns 0 on success or -1 on failure
    # // returns 0 on success or -1 on failure.
    values = args(func_signature, cpu, mem)

    file_obj = file_id = next(values)
    return_value = Integer(-1, SysCallLocation)

    try:
        if file_id not in std_files:
            file_obj = kernel.opened_files.pop(file_id)
            file_obj.flush()
            file_obj.close()
        return_value = Integer(0, SysCallLocation)
    except KeyError as _:
        logger.warning('trying to close a non-opened file_id {f}'.format(f=file_id))
    except Exception as ex:
        logger.warning('failed to close file {f}, error: {m}'.format(f=getattr(file_obj, 'name', file_obj), m=ex))
    __return__(return_value, cpu, mem, kernel)


def __read__(
        cpu,
        mem,
        kernel,
        func_signature=FunctionType(
            IntegerType(SysCallLocation),
            (
                AbstractDeclarator(IntegerType(SysCallLocation), SysCallLocation),
                AbstractDeclarator(PointerType(CharType(SysCallLocation), SysCallLocation), SysCallLocation),
                AbstractDeclarator(
                    LongType(LongType(IntegerType(SysCallLocation), SysCallLocation, unsigned=True), SysCallLocation),
                    SysCallLocation
                )
            ),
            SysCallLocation
        )):
    # int __read__(int file_id, char *dest, unsigned long long number_of_bytes);
    # // returns the number of elements read on success or -1 on failure
    values = args(func_signature, cpu, mem)

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
    __return__(return_value, cpu, mem, kernel)


def __write__(
        cpu,
        mem,
        kernel,
        func_signature=FunctionType(
            IntegerType(SysCallLocation),
            (
                AbstractDeclarator(IntegerType(SysCallLocation), SysCallLocation),
                AbstractDeclarator(PointerType(CharType(SysCallLocation), SysCallLocation), SysCallLocation),
                AbstractDeclarator(
                    LongType(LongType(IntegerType(SysCallLocation), SysCallLocation), SysCallLocation, unsigned=True),
                    SysCallLocation
                )
            ),
            SysCallLocation
        )):
    # int  __write__(int file_id, char *buffer, unsigned long long number_of_bytes);
    # // returns 0 on success or -1 on failure.
    values = args(func_signature, cpu, mem)
    file_id, buffer_ptr, number_of_bytes = values
    return_value = Integer(-1, LocationNotSet)

    values = ''.join(imap(chr, __buffer__(buffer_ptr, number_of_bytes, mem)))
    try:
        file_id = kernel.opened_files[int(file_id)]
        file_id.write(values)
        return_value = Integer(0, LocationNotSet)
    except KeyError as _:
        logger.warning('trying to write to a non-opened file_id {f}'.format(f=file_id))
    except Exception as ex:
        logger.warning('failed to write to file {f}, error: {m}'.format(f=getattr(file_id, 'name', file_id), m=ex))
        return_value = Integer(-1, LocationNotSet)
    __return__(return_value, cpu, mem, kernel)


def __tell__(
        cpu,
        mem,
        kernel,
        func_signature=FunctionType(
            IntegerType(SysCallLocation),
            (AbstractDeclarator(IntegerType(SysCallLocation), SysCallLocation),),
            SysCallLocation
        )):
    # int __tell__(int);
    values = args(func_signature, cpu, mem)
    return_value = Integer(-1, LocationNotSet)
    file_id, = values

    try:
        file_id = kernel.opened_files[file_id]
        return_value = Integer(file_id.tell(), LocationNotSet)
    except KeyError as _:
        logger.warning('trying to ftell on a non-opened file_id {f}'.format(f=file_id))
    except Exception as ex:
        logger.warning('failed to ftell on file {f}, error: {m}'.format(f=getattr(file_id, 'name', file_id), m=ex))
    __return__(return_value, cpu, mem, kernel)


def __seek__(
        cpu,
        mem,
        kernel,
        func_signature=FunctionType(
            IntegerType(SysCallLocation),
            (
                AbstractDeclarator(IntegerType(SysCallLocation), SysCallLocation),
                AbstractDeclarator(IntegerType(SysCallLocation), SysCallLocation),
                AbstractDeclarator(IntegerType(SysCallLocation), SysCallLocation),
            ),
            SysCallLocation
        )):
    # int __seek__(int file_id, int offset, int whence);
    values = args(func_signature, cpu, mem)

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
    __return__(return_value, cpu, mem, kernel)


def __exit__(
        cpu,
        mem,
        kernel,
        func_signature=FunctionType(
            VoidType(SysCallLocation),
            (AbstractDeclarator(IntegerType(SysCallLocation), SysCallLocation),),
            SysCallLocation
        )):

    # void exit(int return_value);
    value, = args(func_signature, cpu, mem)
    # Flush and close all opened files except stdio
    for file_id in ifilter(lambda file_id: file_id not in dict(std_files), kernel.opened_files):
        kernel.opened_files[file_id].flush()
        kernel.opened_files[file_id].close()

    mem[-size(IntegerType())] = value  # Set the return status on top of the stack
    cpu.base_pointer = cpu.stack_pointer = push_integral.core_type(-word_size)  # reset stack/base pointers ...

    mem[cpu.instr_pointer + word_size] = Halt(SysCallLocation)  # Halt machine ...


class SystemCall(Code):
    def __init__(self, name, size, storage_class, location, call_id):
        self._first_element = Push(location, push_integral.core_type(call_id))
        super(SystemCall, self).__init__(
            name,
            (self._first_element, SysCallInstruction(location)),
            size,
            storage_class,
            location
        )

__ids__ = (
    ('__open__', 5, __open__),
    ('__read__', 3, __read__),
    ('__write__', 4, __write__),
    ('__close__', 6, __close__),
    ('__tell__', 198, __tell__),
    ('__seek__', 199, __seek__),
    ('exit', 1, __exit__)
)


SYMBOLS = {call_name: SystemCall(call_name, None, None, SysCallLocation, call_id) for call_name, call_id, _ in __ids__}
CALLS = {call_id: call_code for _, call_id, call_code in __ids__}
