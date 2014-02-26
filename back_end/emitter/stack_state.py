__author__ = 'samyvilar'

from itertools import imap, repeat
from utils.sequences import exhaust
from front_end.parser.types import CType, c_type

from front_end.parser.ast.declarations import Declaration, Declarator

from back_end.emitter.c_types import size
from back_end.virtual_machine.instructions.architecture import load_base_stack_pointer, add, push

from back_end.emitter.expressions.static import bind_load_address_func


class Stack(object):
    def __init__(self):
        self._stack_pointer = 0

    def allocate(self, amount):
        self.stack_pointer -= amount

    def de_allocate(self, amount):
        self.stack_pointer += amount

    @property
    def stack_pointer(self):
        return self._stack_pointer

    @stack_pointer.setter
    def stack_pointer(self, value):
        if value > 0:
            raise ValueError
        self._stack_pointer = value

    def __nonzero__(self):
        return 1


def bind_instructions(obj, offset):
    def load_address(self, location):
        return add(load_base_stack_pointer(location), push(self.offset, location), location)

    obj.offset = offset
    obj.load_address = bind_load_address_func(load_address, obj)
    return obj


def unbind_instructions(obj, offset):
    exhaust(imap(delattr, repeat(obj), ('offset', 'load_address')))
    return obj


def stack_allocation(stack, obj):
    obj_type = obj if isinstance(obj, CType) else c_type(obj)
    stack.allocate(size(obj_type))
    return bind_instructions(obj, stack.stack_pointer) if isinstance(obj, (Declaration, Declarator)) else obj


def stack_de_allocation(stack, obj):
    obj_type = obj if isinstance(obj, CType) else c_type(obj)
    stack.de_allocate(size(obj))
    return unbind_instructions(stack, obj) if isinstance(obj, (Declaration, Declarator)) else obj

