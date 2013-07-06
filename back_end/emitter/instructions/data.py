__author__ = 'samyvilar'

from types import MethodType
from back_end.virtual_machine.instructions.architecture import Push, Address, LoadBaseStackPointer
from back_end.virtual_machine.instructions.architecture import Integer, Add


def bind_instructions(obj, offset):
    def load_address(self, location):
        yield LoadBaseStackPointer(location)
        yield Push(location, Integer(self.offset, location))
        yield Add(location)

    obj.offset = offset
    obj.load_address = MethodType(load_address, obj)
    return obj


def global_allocation(obj):
    def load_address(self, location):
        yield Push(location, Address(self.symbol, location))

    obj.load_address = MethodType(load_address, obj)
    return obj