__author__ = 'samyvilar'

from front_end.parser.types import CType, c_type

from front_end.parser.ast.declarations import Declaration, Declarator

from back_end.emitter.types import size
from back_end.emitter.instructions.data import bind_instructions


class Stack(list):
    def __init__(self):
        self._stack_pointer = 0
        super(Stack, self).__init__()

    def save_stack_pointer(self):
        self.append(self.stack_pointer)

    def restore_stack_pointer(self):
        self.stack_pointer = self.pop()

    @property
    def stack_pointer(self):
        return self._stack_pointer

    @stack_pointer.setter
    def stack_pointer(self, value):
        if value < 0:
            raise ValueError
        self._stack_pointer = value

    def allocate(self, allocation_size):
        self.stack_pointer += allocation_size


def stack_allocation(stack, obj):
    if isinstance(obj, CType):
        obj_type = obj
    else:
        obj_type = c_type(obj)

    allocation_size, offset = size(obj_type), stack.stack_pointer

    stack.allocate(allocation_size)

    return bind_instructions(obj, offset) if isinstance(obj, (Declaration, Declarator)) else obj


def stack_de_allocation(stack, obj):
    if isinstance(obj, CType):
        obj_type = obj
    else:
        obj_type = c_type(obj)

    stack.allocate(-1 * size(obj_type))
