__author__ = 'samyvilar'

from types import MethodType

from front_end.parser.types import c_type, ArrayType

from back_end.virtual_machine.instructions.architecture import Push, Address, Load, LoadBaseStackPointer
from back_end.virtual_machine.instructions.architecture import Integer, Add
from back_end.emitter.types import size


def _load_instructions(self, location):
    return (self.load_address(location) if isinstance(c_type(self), ArrayType)
            else (self.load_address(location) + [Load(location, size(c_type(self)))]))


def bind_instructions(obj, offset):
    def load_address(self, location):
        return [
            LoadBaseStackPointer(location),
            Push(location, Integer(-1 * self.offset, location)),
            Add(location),
        ]

    obj.offset = offset
    obj.load_address = MethodType(load_address, obj)
    obj.load_instructions = MethodType(_load_instructions, obj)
    return obj


def global_allocation(obj):
    def load_address(self, location):
        return [Push(location, Address(self.symbol, location))]

    obj.load_address = MethodType(load_address, obj)
    obj.load_instructions = MethodType(_load_instructions, obj)

    return obj


def load_instructions(obj, location):
    return getattr(obj, 'load_instructions')(location)


def safe_guard(value):
    assert value