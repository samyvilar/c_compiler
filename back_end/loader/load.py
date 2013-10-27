__author__ = 'samyvilar'

from front_end.loader.locations import loc
from back_end.virtual_machine.instructions.architecture import Address


def load(elem_seq, mem):
    references = []
    for element in elem_seq:
        mem[element.address] = element
        # Keep track of references, they have yet to be updated with the correct value ...
        if isinstance(element, Address):  # Data, Symbol, Instruction or Goto ...
            if not isinstance(element.obj, (int, long)):
                references.append(element)

    for ref in references:
        # make sure the obj has being properly replaced with an Integer Constant ...
        if not isinstance(ref.obj, (int, long)):
            raise ValueError('{l} Expected an int/long got {g}'.format(l=loc(ref), g=type(ref.obj)))
        mem[ref.address] = ref.obj
