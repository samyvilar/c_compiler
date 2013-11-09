__author__ = 'samyvilar'

#raise ImportError
import os
import sys

from ctypes import c_ulonglong, c_uint, Structure, POINTER, CDLL, CFUNCTYPE, byref, c_int, c_char_p, c_void_p
from ctypes import c_float, c_double, cast, sizeof, addressof, pointer
from ctypes import pythonapi, py_object
from struct import pack, unpack

from back_end.virtual_machine.instructions.architecture import Double, Push, Address, operns
from back_end.virtual_machine.instructions.architecture import Allocate, Dup, Swap, Load, Set

from logging_config import logging

logger = logging.getLogger('virtual_machine')

word_type, word_format = c_ulonglong, 'Q'
float_type, float_format = c_double, 'd'
# word_type, word_format = c_uint, 'I'
# float_type, float_format = c_float, 'f'

word_size = sizeof(word_type)


try:
    libvm = CDLL(os.path.join(os.path.dirname(__file__), 'libvm.so'))
except OSError as er:
    logger.warning(er)
    logger.warning("Could not load C virtual machine, please run make or make build-icc at back_end/virtual_machine/c")
    raise ImportError


# class frame_type(Structure):
#     pass
# frame_type.__fields__ = [('next', POINTER(frame_type)), ('base_pointer', word_type), ('stack_pointer', word_type)]

vm_number_of_addressable_words = word_type.in_dll(libvm, 'vm_number_of_addressable_words').value


class CPU(Structure):
    _fields_ = [('stack_pointer', word_type),
                ('base_pointer', word_type),
                ('instr_pointer', word_type),
                ('flags', word_type)]

    def __init__(self):
        super(CPU, self).__init__()
        self.stack_pointer = word_type(-1)
        self.base_pointer = word_type(-1)
        self.frames = None


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

# kernel_type *new_kernel(FUNC_SIGNATURE((*sys_calls[256])), file_node_type *opened_files, virtual_memory_type *mem)
#libvm.new_kernel.argtypes = [POINTER(FUNC_SIGNATURE), POINTER(file_node_type)]
#libvm.new_kernel.argtypes = [256 * POINTER(FUNC_SIGNATURE), POINTER(file_node_type), POINTER(virtual_memory_type)]
#libvm.new_kernel.restype = POINTER(kernel_type)
#libvm.new_file_node.argtypes = [POINTER(virtual_memory_type), word_type, c_void_p, POINTER(file_node_type)]
#libvm.new_file_node.restype = POINTER(file_node_type)

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
            # libvm.new_file_node(
            #     None,
            #     word_type(file_id),
            #     PyFile_AsFile(file_obj),
            #     # libvm.fdopen(c_int(file_obj.fileno()), c_char_p(file_obj.mode)),
            #     self.c_kernel_p.contents.opened_files
            # )

libvm.evaluate.argtypes = [POINTER(CPU), POINTER(virtual_memory_type), POINTER(kernel_type)]

# libvm.new_virtual_memory.argtypes = []
# libvm.new_virtual_memory.restype = POINTER(virtual_memory_type)
#
# libvm._set_word_.argtypes = [POINTER(virtual_memory_type), word_type, word_type]
# libvm._get_word_.argtypes = [POINTER(virtual_memory_type), word_type]
# libvm._get_word_.restype = word_type


# class VirtualMemory(object):
#     def __init__(self, factory_type=None, c_virtual_memory_pointer=None):
#         self.factory_type = factory_type or word_type
#         self.c_vm_p = c_virtual_memory_pointer or libvm.new_virtual_memory()
#         self.code = {}
#
#     def __setitem__(self, key, value):
#         self.code[key] = value
#         if isinstance(value, Double):
#             value = unpack(word_format, pack(float_format, float(value)))[0]
#         libvm._set_word_(self.c_vm_p, self.factory_type(key), self.factory_type(value))
#
#     def __getitem__(self, item):
#         return libvm._get_word_(self.c_vm_p, self.factory_type(item))
#
#
# def c_evaluate(cpu, mem, os=None):
#     libvm.evaluate(
#         byref(cpu),
#         mem.c_vm_p,
#         os and os.c_kernel_p or libvm.new_kernel(c_void_p(), c_void_p(), c_void_p())
#     )


libvm.allocate_entire_physical_address_space.argtypes = []
libvm.allocate_entire_physical_address_space.restype = POINTER(word_type)


shared_c_physical_memory_pointer = libvm.allocate_entire_physical_address_space()


class VirtualMemory(object):
    def __init__(self, factory_type=None, c_physical_memory_pointer=None):
        self.factory_type = factory_type or word_type
        self.c_vm_p = c_physical_memory_pointer or libvm.allocate_entire_physical_address_space()
        self.start_of_physical_addr = cast(self.c_vm_p, c_void_p).value
        self.end_of_physical_addr = \
            self.start_of_physical_addr + ((vm_number_of_addressable_words - 1) * sizeof(self.factory_type))
        if self.start_of_physical_addr == -1 or self.start_of_physical_addr == 0:
            raise ValueError('{l} Failed to pre-allocate entire virtual address space ...')
        self.code = {}
        self.start_of_virtual_addr = vm_number_of_addressable_words

        self.pushed_addresses = {}
        self.instrs_word_operands = {}

    def __setitem__(self, key, value):
        assert key < vm_number_of_addressable_words
        if key < self.start_of_virtual_addr:  # keep track of the smallest virtual address ... (need to make sure its 0)
            self.start_of_virtual_addr = key

        self.code[key] = value  # record instructions in python for debugging purposes ...
        if isinstance(value, Double):
            value = unpack(word_format, pack(float_format, float(value)))[0]

        if isinstance(value, (Allocate, Dup, Swap, Load, Set)):  # this machine counts in words ... we need to update
            self.instrs_word_operands[key] = value

        if isinstance(value, Address):
            self.pushed_addresses[key] = value
            if not isinstance(self.code.get(key - 1, None), Push):
                pass

        self.c_vm_p[key] = self.factory_type(value)

    def __getitem__(self, addr):
        return cast(addr, POINTER(word_type))[0]


# libvm.evaluate_without_vm.argtypes = libvm.evaluate.argtypes


def c_evaluate(cpu, mem, os=None):
    cpu.instr_pointer = mem.start_of_physical_addr
    cpu.base_pointer = cpu.stack_pointer = mem.end_of_physical_addr

    for v_addr, instr in mem.pushed_addresses.iteritems():  # translate all virtual addresses ...
        if isinstance(instr, Address):
            mem.c_vm_p[v_addr] = mem.factory_type(mem.start_of_physical_addr + (instr.obj * sizeof(word_type)))

    for virtual_addr, instr in mem.instrs_word_operands.iteritems():  # update operands since machine will use word
        mem[virtual_addr + 1] = long(operns(instr)[0])/word_size

    # from front_end.loader.locations import loc
    # for instr in mem.code.itervalues():
    #     print loc(instr), instr

    libvm.evaluate(
        byref(cpu),
        mem.c_vm_p,
        (os and os.c_kernel_p) or Kernel().c_kernel_p
    )

    cpu.instr_pointer = cpu.instr_pointer
    cpu.base_pointer = cpu.base_pointer
    cpu.stack_pointer = cpu.stack_pointer