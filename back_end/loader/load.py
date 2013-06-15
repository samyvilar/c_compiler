__author__ = 'samyvilar'

from itertools import izip, imap

from front_end.loader.locations import loc, Location
from back_end.emitter.types import flatten
from back_end.emitter.object_file import Symbol, Code, binaries
from back_end.virtual_machine.instructions.architecture import Address, Instruction, Halt
from back_end.virtual_machine.instructions.stack import _push, _push_frame
from back_end.virtual_machine.memory import VirtualMemory
from back_end.virtual_machine.cpu.core import CPU
from back_end.virtual_machine.machine import VirtualMachine
from back_end.linker.link import name

from back_end.virtual_machine.instructions.encoder import encode, addresses


def load(binary_file):
    symbol_table, bins, entry_point = binary_file.symbol_table, binary_file.bins, binary_file.entry_point
    mem, cpu = VirtualMemory(), CPU()
    zero, one = cpu.word_type(0), cpu.word_type(1)

    halt_address = zero
    bins.append(Halt(Location('__EOP__', -1, -1)))
    for instr, elem, addr in izip(flatten(bins), encode(bins, cpu.word_type), addresses(zero, one)):
        mem[addr] = elem
        halt_address = instr.address = addr

    for elem in flatten(bins):  # Set all references to symbols/instructions for jumps.
        if isinstance(elem, Address):
            if isinstance(elem.obj, Symbol):
                addr = next(flatten(bins[symbol_table[name(elem.obj)].offset])).address
            elif isinstance(elem.obj, Instruction):
                addr = elem.obj.address
            else:
                addr = elem
            mem[elem.address] = addr

    # Allocate main return value, and return halt address.
    _push(zero, cpu, mem)
    _push_frame(None, cpu, mem)
    _push(halt_address, cpu, mem)

    cpu.instr_pointer = next(flatten(binaries(symbol_table[entry_point]))).address
    if not isinstance(symbol_table[entry_point], Code):
        raise ValueError('{l} an entry point must be a code object, got {g}'.format(
            l=loc(symbol_table[entry_point]), g=symbol_table[entry_point],
        ))
    return VirtualMachine(mem, cpu)




