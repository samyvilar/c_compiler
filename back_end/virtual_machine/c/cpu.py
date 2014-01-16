__author__ = 'samyvilar'

# raise ImportError
import os
import sys

from itertools import imap

from ctypes import c_ulonglong, c_uint, Structure, POINTER, CDLL, CFUNCTYPE, byref, c_int, c_char_p, c_void_p
from ctypes import c_float, c_double, cast, sizeof, addressof, pointer, c_ushort, c_ubyte
from ctypes import pythonapi, py_object
from struct import pack, unpack

from back_end.virtual_machine.instructions.architecture import Double, Address, operns
from back_end.virtual_machine.instructions.architecture import Allocate, Dup, Swap, Load, Set, Offset

from logging_config import logging

logger = logging.getLogger('virtual_machine')

sorted_word_types, sorted_float_types = (c_ulonglong, c_uint, c_ushort, c_ubyte), (c_double, c_float)
word_type, half_word_type, quarter_word_type, one_eighth_word_type = sorted_word_types
word_format, half_word_format, quarter_word_format, one_eighth_word_format = 'Q', 'I', 'H', 'B'
word_size, half_word_size, quarter_word_size, one_eighth_word_size = imap(
    sizeof, (c_ulonglong, c_uint, c_ushort, c_ubyte)
)

float_type, half_float_type = sorted_float_types
float_format, half_float_format = 'd', 'f'


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
        if isinstance(value, Double):
            value = unpack(word_format, pack(float_format, float(value)))[0]  # re-interpret floats as machine words ...

        if isinstance(value, (Dup, Swap, Load, Set)):  # this instrs count in words ... we need to update ...
            self.instrs_word_operands[key] = value

        # keep track of address since they need to be translated from virtual to phys
        if isinstance(value, Address):
            self.addresses[key] = value

        cast(self.start_of_physical_addr + key, POINTER(word_type))[0] = self.factory_type(value)

    def __getitem__(self, addr):
        return cast(addr, POINTER(word_type))[0]


# libvm.evaluate_without_vm.argtypes = libvm.evaluate.argtypes


def c_evaluate(cpu, mem, os=None):
    cpu.instr_pointer = mem.start_of_physical_addr
    cpu.base_pointer = cpu.stack_pointer = mem.end_of_physical_addr

    for v_addr, addr in mem.addresses.iteritems():  # translate all virtual addresses ...
        mem[v_addr] = mem.start_of_physical_addr + addr.obj

    for virtual_addr, instr in mem.instrs_word_operands.iteritems():  # update operands since machine will use word
        mem[virtual_addr + word_size] = long(operns(instr)[0])/word_size

    if os is None:
        os = Kernel()

    libvm.evaluate(byref(cpu), mem.c_vm_p, os.c_kernel_p)

    cpu.instr_pointer = cpu.instr_pointer
    cpu.base_pointer = cpu.base_pointer
    cpu.stack_pointer = cpu.stack_pointer


def base_element(cpu, mem, element_size):
    return mem[cpu.base_pointer - element_size]