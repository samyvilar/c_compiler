__author__ = 'samyvilar'

# raise ImportError
import os
import sys
from ctypes import c_ulonglong, c_uint, Structure, POINTER, CDLL, CFUNCTYPE, byref, c_int, c_char_p, c_void_p
from ctypes import c_float, c_double
from ctypes import pythonapi, py_object
from struct import pack, unpack

from logging_config import logging

logger = logging.getLogger('virtual_machine')

word_type, word_format = c_ulonglong, 'Q'
float_type, float_format = c_double, 'd'
# word_type, word_format = c_uint, 'I'
# float_type, float_format = c_float, 'f'
try:
    libvm = CDLL(os.path.join(os.path.dirname(__file__), 'libvm.so'))
except OSError as er:
    logger.warning(er)
    logger.warning("Could not load C virtual machine, please run make or make build-icc at back_end/virtual_machine/c")
    raise ImportError


class frame_type(Structure):
    pass
frame_type.__fields__ = [('next', POINTER(frame_type)), ('base_pointer', word_type), ('stack_pointer', word_type)]


class CPU(Structure):
    _fields_ = [('stack_pointer', word_type),
                ('base_pointer', word_type),
                ('instr_pointer', word_type),
                ('zero_flag', word_type),
                ('carry_borrow_flag', word_type),
                ('most_significant_bit_flag', word_type),
                ('frames', POINTER(frame_type))]

    def __init__(self):
        super(CPU, self).__init__()
        self.stack_pointer = word_type(-1)
        self.base_pointer = word_type(-1)
        self.frames = None


virtual_memory_type = None


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
file_node_type._fields_ = [('next', POINTER(file_node_type)), ('file_id', word_type), ('file_pointer', c_void_p)]


class kernel_type(Structure):
    pass
FUNC_SIGNATURE = CFUNCTYPE(None, POINTER(CPU), POINTER(virtual_memory_type), POINTER(kernel_type))
kernel_type._fields_ = [('calls', 256 * POINTER(FUNC_SIGNATURE)), ('opened_files', POINTER(file_node_type))]
libvm.new_kernel.argtypes = [256 * POINTER(FUNC_SIGNATURE), POINTER(file_node_type), POINTER(virtual_memory_type)]
libvm.new_kernel.restype = POINTER(kernel_type)

libvm.new_file_node.argtypes = [POINTER(virtual_memory_type), word_type, c_void_p, POINTER(file_node_type)]
libvm.new_file_node.restype = POINTER(file_node_type)

libvm.fdopen.argtypes = [c_int, c_char_p]
libvm.fdopen.restype = c_void_p


class Kernel(object):
    def __init__(self, calls=None, c_kernel_pointer=None):
        self.c_kernel_p = c_kernel_pointer or libvm.new_kernel(None, None, None)
        self.opened_files = {
            getattr(sys.stdin, 'fileno', lambda: 0)(): sys.stdin,
            getattr(sys.stdout, 'fileno', lambda: 1)(): sys.stdout,
            getattr(sys.stderr, 'fileno', lambda: 2)(): sys.stderr,
        }

    @property
    def opened_files(self):
        return self._opened_files

    @opened_files.setter
    def opened_files(self, files):
        self._opened_files = files
        self.c_kernel_p.contents.opened_files = None
        for file_id, file_obj in files.iteritems():
            self.c_kernel_p.contents.opened_files = libvm.new_file_node(
                None,
                word_type(file_id),
                PyFile_AsFile(file_obj),
                # libvm.fdopen(c_int(file_obj.fileno()), c_char_p(file_obj.mode)),
                self.c_kernel_p.contents.opened_files
            )

libvm.evaluate.argtypes = [POINTER(CPU), POINTER(virtual_memory_type), POINTER(kernel_type)]
libvm.new_virtual_memory.argtypes = []
libvm.new_virtual_memory.restype = POINTER(virtual_memory_type)

# kernel_type *new_kernel(FUNC_SIGNATURE((*sys_calls[256])), file_node_type *opened_files, virtual_memory_type *mem)
libvm.new_kernel.argtypes = [POINTER(FUNC_SIGNATURE), POINTER(file_node_type), POINTER(virtual_memory_type)]
libvm.new_kernel.restype = POINTER(kernel_type)

libvm._set_word_.argtypes = [POINTER(virtual_memory_type), word_type, word_type]
libvm._get_word_.argtypes = [POINTER(virtual_memory_type), word_type]
libvm._get_word_.restype = word_type


class VirtualMemory(object):
    def __init__(self, factory_type=None, c_virtual_memory_pointer=None):
        self.factory_type = factory_type or word_type
        self.c_vm_p = c_virtual_memory_pointer or libvm.new_virtual_memory()
        self.code = {}

    def __setitem__(self, key, value):
        self.code[key] = value
        if isinstance(value, float):
            value = unpack(word_format, pack(float_format, value))[0]
        libvm._set_word_(self.c_vm_p, self.factory_type(key), self.factory_type(value))

    def __getitem__(self, item):
        return libvm._get_word_(self.c_vm_p, self.factory_type(item))


def c_evaluate(cpu, mem, os=None):
    libvm.evaluate(
        byref(cpu),
        mem.c_vm_p,
        os and os.c_kernel_p or libvm.new_kernel(None, None, None)
    )