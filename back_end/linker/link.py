__author__ = 'samyvilar'

from itertools import chain

from front_end.parser.symbol_table import SymbolTable
from back_end.emitter.object_file import Data, Code
from back_end.emitter.c_types import size

from back_end.virtual_machine.instructions.architecture import Push, PushFrame, PopFrame, Halt, Integer, Allocate
from back_end.virtual_machine.instructions.architecture import RelativeJump, Pass, Address


def binaries(symbol, symbol_table):
    def set_address(symbol, binaries):
        initial_instr = next(binaries)
        yield initial_instr
        for instr in binaries:
            yield instr
        symbol.address = initial_instr.address

    if symbol.binaries:  # definition
        symbol_table[symbol.name] = symbol
        symbol.binaries = set_address(symbol, symbol.binaries)
    else:
        if isinstance(symbol, Data) and not symbol.storage_class:  # declaration.
            # C coalesces multiple declarations across multiple files as long as they don't have a storage class
            if symbol.name in symbol_table:  # only keep largest.
                if symbol.size > symbol_table[symbol.name].size:
                    _ = symbol_table.pop(symbol.name)
                    symbol_table[symbol.name] = symbol
            else:
                symbol_table[symbol.name] = symbol
    return symbol.binaries


def executable(symbols, symbol_table=None):
    """
        push(0, self.cpu, self.mem)  # return address
        push(0, self.cpu, self.mem)  # main function address
        push_frame(None, self.cpu, self.mem)  # create new frame
        halt_address = next(address_gen)
        self.mem[halt_address] = Halt('__EOP__')
        push(halt_address, self.cpu, self.mem)
        self.cpu.instr_pointer = symbol_table['main'].address
        evaluate(self.cpu, self.mem)
        pop_frame(None, self.cpu, self.mem)
        pop(self.cpu, self.mem)  # Pop address
        pop(self.cpu, self.mem)  # Pop return value.2

    """
    location = '__SOP__'
    clean = Pass(location)
    return chain(
        (
            Push(location, Integer(0, location)),  # return value
            Push(location, Address(0, location)),  # address of main function
            PushFrame(location),
            Push(location, Address(clean, location)),  # clean up after main exits
            RelativeJump(location, Address(Code('main', (), 1, None, location))),  # jump to main
        ),
        chain.from_iterable(binaries(symbol, symbol_table or SymbolTable()) for symbol in symbols),
        (
            clean,
            PopFrame(location),
            Allocate(location, -1 * size(Address())),
            Allocate(location, -1 * size(Integer(0, location))),
            Halt(location)
        ),
    )