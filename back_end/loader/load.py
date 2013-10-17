__author__ = 'samyvilar'

from types import NoneType
from front_end.loader.locations import loc
from back_end.emitter.object_file import Reference
from back_end.virtual_machine.instructions.architecture import Address, Instruction, Integer, Operand


def load(elem_seq, mem):
    address = []
    for element in elem_seq:
        mem[element.address] = element
        # Keep track of references, they have yet to be updated with the correct value ...
        if isinstance(element, Address):  # Data, Symbol, Instruction or Goto ...
            if isinstance(element.obj, (Operand, Reference, Instruction, NoneType)):
                address.append(element)

    for addr in address:
        # make sure the obj has being properly replaced with an Integer Constant ...
        if not isinstance(addr.obj, Integer):
            raise ValueError('{l} Expected Integer got {g}'.format(l=loc(addr), g=type(addr.obj)))
        mem[addr.address] = addr.obj
