__author__ = 'samyvilar'

from back_end.emitter.object_file import Reference
from back_end.virtual_machine.instructions.architecture import Address, Instruction, Byte, RelativeJump


def addresses(curr=1, step=1, encoder=int):
    while True:
        yield encoder(curr)
        curr += step


def load(instrs, symbol_table, mem, address_gen=None, encoder=int):
    address_gen = iter(address_gen or addresses(encoder=lambda addr: encoder(Address(addr))))

    references = {}
    for elem in instrs:
        elem.address = next(address_gen)
        mem[elem.address] = encoder(elem)
        if isinstance(elem, Address):
            references[elem.address] = elem

    for addr, elem in references.iteritems():
        if isinstance(elem.obj, Instruction):
            mem[addr] = elem.obj.address
        elif isinstance(elem.obj, Reference):
            symbol = symbol_table[elem.obj.name]
            if hasattr(symbol, 'first_element'):
                mem[addr] = symbol.first_element.address
            else:
                symbol.first_element = Byte(0, '')
                symbol.first_element.address = next(address_gen)
                mem[symbol.first_element.address] = symbol.first_element
                for _ in xrange(symbol.size - 1):
                    mem[next(address_gen)] = encoder(Byte(0, ''))
        if mem[addr - 1] == encoder(RelativeJump(0, '')):
            mem[addr] -= addr - 1