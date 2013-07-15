__author__ = 'samyvilar'

from itertools import izip

from front_end.loader.locations import loc, Location
from back_end.emitter.object_file import Symbol, Code, binaries

from back_end.virtual_machine.instructions.architecture import Address, Instruction, Byte, RelativeJump, ids


def addresses(curr=0, step=1, encoder=int):
    while True:
        yield encoder(curr)
        curr += step


def load(byte_seq, symbol_table, mem, address_gen=None, encoder=int):
    address_gen = iter(address_gen or addresses(encoder=lambda addr: encoder(Address(addr))))

    references = {}
    for elem in byte_seq:
        elem.address = next(address_gen)
        mem[elem.address] = encoder(elem)
        if isinstance(elem, Address):
            references[elem.address] = elem

    for addr, elem in references.iteritems():
        if isinstance(elem.obj, Instruction):
            mem[addr] = elem.obj.address
        elif isinstance(elem.obj, Symbol):
            symbol = symbol_table[elem.obj.name]
            if hasattr(symbol, 'address'):
                mem[addr] = symbol.address
            else:
                symbol.address = next(address_gen)
                mem[symbol.address] = encoder(Byte(0, ''))
                for _ in xrange(symbol.size - 1):
                    mem[next(address_gen)] = encoder(Byte(0, ''))
        if mem[addr - 1] == encoder(RelativeJump(0, '')):
            mem[addr] -= addr - 1