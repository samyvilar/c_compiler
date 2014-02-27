__author__ = 'samyvilar'

# raise ImportError
import os
import sys
import inspect

from itertools import imap, izip, chain, repeat, ifilter, izip_longest

from ctypes import c_ulonglong, c_uint, Structure, POINTER, CDLL, CFUNCTYPE, byref, c_int, c_char_p, c_void_p
from ctypes import c_float, c_double, cast, sizeof, pointer, c_ushort, c_ubyte, c_longlong, c_short, c_byte
from ctypes import pythonapi, py_object

import struct
from struct import pack, unpack

import back_end.virtual_machine.instructions.architecture as architecture
from back_end.virtual_machine.instructions.architecture import Address, RealOperand
from back_end.virtual_machine.instructions.architecture import Word, Half, Quarter, OneEighth, DoubleHalf, Double

from loggers import logging

logger = logging.getLogger('virtual_machine')
current_module = sys.modules[__name__]

word_names = tuple((p + 'word') for p in ('', 'half_', 'quarter_', 'one_eighth_'))
signed_word_names = tuple(imap('signed_'.__add__, word_names))
float_names = 'float', 'half_float'

word_factories = c_ulonglong, c_uint, c_ushort, c_ubyte
signed_word_factories = c_longlong, c_int, c_short, c_byte
float_factories = c_double, c_float

word_formats = 'Q', 'I', 'H', 'B'
signed_word_formats = tuple(imap(str.lower, word_formats))
float_formats = 'd', 'f'


kind_of_types = 'word', 'signed_word', 'float'


def get_info_on_kind(type_kind, info_name):
    return globals()['{kind}_{info}'.format(kind=type_kind, info=info_name)]


def get_type_names(type_kind):
    return get_info_on_kind(type_kind, 'names')


def get_type_factories(type_kind):
    return get_info_on_kind(type_kind, 'factories')


def get_type_formats(type_kind):
    return get_info_on_kind(type_kind, 'formats')


word_type_factories = dict(
    chain.from_iterable(imap(izip, imap(get_type_names, kind_of_types), imap(get_type_factories, kind_of_types)))
)

word_type_sizes = dict(izip(word_type_factories.iterkeys(), imap(sizeof, word_type_factories.itervalues())))


word_type_formats = dict(
    chain.from_iterable(imap(izip, imap(get_type_names, kind_of_types), imap(get_type_formats, kind_of_types)))
)


for word_type_name in word_type_factories:
    setattr(sys.modules[__name__], word_type_name + '_size', word_type_sizes[word_type_name])
    setattr(sys.modules[__name__], word_type_name + '_type', word_type_factories[word_type_name])
    setattr(sys.modules[__name__], word_type_name + '_format', word_type_formats[word_type_name])


try:
    libvm = CDLL(os.path.join(os.path.dirname(__file__), 'libvm.so'))
except OSError as er:
    logger.warning(er)
    logger.warning("Could not load C virtual machine, please run `make` or `make build-icc` back_end/virtual_machine/c")
    raise ImportError


vm_number_of_addressable_words = word_type.in_dll(libvm, 'vm_number_of_addressable_words').value


class CPU(Structure):
    _fields_ = [('stack_pointer', word_type),
                ('base_pointer', word_type),
                ('instr_pointer', word_type),
                ('flags', word_type)]


virtual_memory_type = word_type


class FILE(Structure):
    pass
FILE_ptr = POINTER(FILE)

PyFile_FromFile = pythonapi.PyFile_FromFile
PyFile_FromFile.restype = py_object
PyFile_FromFile.argtypes = [FILE_ptr, c_char_p, c_char_p, CFUNCTYPE(c_int, FILE_ptr)]

PyFile_AsFile = pythonapi.PyFile_AsFile
PyFile_AsFile.restype = FILE_ptr
PyFile_AsFile.argtypes = [py_object]


class file_node_type(Structure):
    pass
file_node_type._fields_ = [('next', POINTER(file_node_type)), ('file_id', word_type), ('file_pointer', FILE_ptr)]


class kernel_type(Structure):
    pass
FUNC_SIGNATURE = CFUNCTYPE(None, POINTER(CPU), POINTER(virtual_memory_type), POINTER(kernel_type))
kernel_type._fields_ = [('calls', 256 * POINTER(FUNC_SIGNATURE)), ('opened_files', POINTER(file_node_type))]

libvm.fdopen.argtypes = [c_int, c_char_p]
libvm.fdopen.restype = c_void_p


class Kernel(object):
    def __init__(
            self,
            calls=None,
            c_kernel_pointer=None,
            open_files=(
                (getattr(sys.stdin, 'fileno', lambda: 0)(), sys.stdin),
                (getattr(sys.stdout, 'fileno', lambda: 1)(), sys.stdout),
                (getattr(sys.stderr, 'fileno', lambda: 2)(), sys.stderr),
            )
    ):
        self.c_kernel_p = c_kernel_pointer or pointer(kernel_type())
        self.opened_files = dict(open_files)

    @property
    def opened_files(self):
        return self._opened_files

    @opened_files.setter
    def opened_files(self, files):
        self.file_node_objects = []  # we need to keep track of the file_node objects or they will be garbage collected
        self._opened_files = files
        self.c_kernel_p.contents.opened_files = POINTER(file_node_type)()
        for file_id, file_obj in files.iteritems():
            self.file_node_objects.append(
                file_node_type(
                    self.c_kernel_p.contents.opened_files,
                    word_type(file_id),
                    PyFile_AsFile(file_obj),
                )
            )
            self.c_kernel_p.contents.opened_files = pointer(self.file_node_objects[-1])
libvm.evaluate.argtypes = [POINTER(CPU), POINTER(virtual_memory_type), POINTER(kernel_type)]
libvm.allocate_entire_physical_address_space.argtypes = []
libvm.allocate_entire_physical_address_space.restype = POINTER(word_type)


# Allocate entire virtual memory space so it can be shared across multiple uses ...
shared_c_physical_memory_pointer = libvm.allocate_entire_physical_address_space()

architecture_types = set(
    ifilter(
        lambda cls: inspect.isclass(cls)
        and issubclass(cls, architecture.Operand)
        and cls not in {architecture.Operand, architecture.RealOperand},
        imap(getattr, repeat(architecture), dir(architecture))
    )
)

architecture_float_types = set(ifilter(
    lambda cls: issubclass(cls, RealOperand) and cls is not RealOperand, architecture_types
))
architecture_integral_types = architecture_types - architecture_float_types


def architecture_word_name(cls):
    signed = 'signed_'
    if issubclass(cls, OneEighth):
        return signed + 'one_eighth_word'
    elif issubclass(cls, Half):
        return signed + 'half_word'
    elif issubclass(cls, Quarter):
        return signed + 'quarter_word'
    elif issubclass(cls, Word):
        return signed + 'word'
    elif issubclass(cls, DoubleHalf):
        return 'half_float'
    elif issubclass(cls, Double):
        return 'float'
    else:
        raise ValueError('{c} could not be identified!'.format(c=cls))

architecture_type_to_word_type = dict(izip(architecture_types, imap(architecture_word_name, architecture_types)))


def get_bytes(value):
    try:
        return pack(word_type_formats[architecture_type_to_word_type[type(value)]], value)
    except struct.error as er:
        return pack(word_type_formats[architecture_type_to_word_type[type(value)]].upper(), value)


def pack_binaries(elements, to_type=Word):
    assert sys.byteorder == 'little'  # TODO: deal with 'big' endianness where the zeros need to be pre-appended
    assert not word_type_sizes[architecture_type_to_word_type[to_type]] % min(word_type_sizes.itervalues())
    return imap(to_type, chain.from_iterable(imap(  # unpack returns a tuple ...
        unpack,
        repeat(word_type_formats[architecture_type_to_word_type[to_type]]),
        imap(
            ''.join,
            izip_longest(
                *repeat(
                    chain.from_iterable(imap(get_bytes, iter(elements))),
                    word_type_sizes[architecture_type_to_word_type[to_type]]/min(word_type_sizes.itervalues())
                ),
                fillvalue=pack(word_type_formats[min(word_type_sizes.iteritems(), key=lambda i: i[1])[0]], 0)
            )
        )
    )))  # the fillvalue will be appended which is OK for little endian but NOT for BIG endian!!!


class VirtualMemory(object):
    def __init__(self, factory_type=None, c_physical_memory_pointer=None):
        self.factory_type = factory_type or word_type
        self.c_vm_p = c_physical_memory_pointer or shared_c_physical_memory_pointer
        self.start_of_physical_addr = cast(self.c_vm_p, c_void_p).value

        self.end_of_physical_addr = \
            self.start_of_physical_addr + (vm_number_of_addressable_words * sizeof(self.factory_type))

        if self.start_of_physical_addr == -1 or self.start_of_physical_addr == 0:
            raise ValueError('{l} Failed to pre-allocate entire virtual address space ...')

        self.code = {}
        self.start_of_virtual_addr = 0

        self.addresses = {}
        self.instrs_word_operands = {}

    def __setitem__(self, key, value):
        assert key < vm_number_of_addressable_words
        if key < self.start_of_virtual_addr:  # keep track of the smallest virtual address ... (need to make sure its 0)
            self.start_of_virtual_addr = key

        self.code[key] = value  # record instructions in python for debugging purposes ...

        if isinstance(value, RealOperand):
            value = next(pack_binaries((value,)))

        # keep track of address since they need to be translated from virtual to phys
        if isinstance(value, Address):
            self.addresses[key] = value

        cast(self.start_of_physical_addr + key, POINTER(word_type))[0] = self.factory_type(value)

    def __getitem__(self, addr, element_type):
        return cast(addr, POINTER(element_type))[0]

    def update(self, values, **kwargs):
        for key, value in chain(getattr(values, 'iteritems', lambda v=values: v)(), kwargs.iteritems()):
            self[key] = value


# libvm.evaluate_without_vm.argtypes = libvm.evaluate.argtypes


def c_evaluate(cpu, mem, os=None):
    cpu.instr_pointer = mem.start_of_physical_addr
    cpu.base_pointer = cpu.stack_pointer = mem.end_of_physical_addr

    # translate all virtual addresses ...
    mem.update((v_addr, mem.start_of_physical_addr + addr.obj) for v_addr, addr in mem.addresses.iteritems())

    libvm.evaluate(byref(cpu), mem.c_vm_p, (Kernel() if os is None else os).c_kernel_p)

    cpu.instr_pointer = cpu.instr_pointer
    cpu.base_pointer = cpu.base_pointer
    cpu.stack_pointer = cpu.stack_pointer


def base_element(cpu, mem, element_type):
    return mem.__getitem__(cpu.base_pointer - sizeof(element_type), element_type)