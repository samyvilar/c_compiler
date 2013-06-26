__author__ = 'samyvilar'

from front_end.loader.locations import loc
from front_end.parser.ast.declarations import Extern

from back_end.emitter.object_file import Data, Code, binaries, Symbol
from back_end.virtual_machine.instructions.architecture import SaveStackPointer, RestoreStackPointer, Instruction
from back_end.virtual_machine.instructions.architecture import Integer
from back_end.linker.binary_file import BinaryFile
from back_end.emitter.types import flatten


class SymbolTable(dict):
    def __setitem__(self, key, value):
        if key in self:
            raise ValueError('{l} Duplicate symbol {symbol}'.format(l=loc(key), symbol=key))
        super(SymbolTable, self).__setitem__(key, value)

    def __getitem__(self, item):
        if item not in self:
            raise ValueError('{l} Could not locate symbol {symbol}'.format(l=loc(item), symbol=item))
        return super(SymbolTable, self).__getitem__(item)


def ident(symbol):
    return symbol.name


def name(symbol, func_name='', scope_level=0, scope_depth=0):
    if isinstance(symbol.storage_class, Extern) or not symbol.storage_class:
        return ident(symbol)  # we don't mangle extern or shared variables.
    # Name mangling ...
    return '{file_name}.{fund_name}.{scope_level}.{scope_depth}.{ident_name}'.format(
        file_name=loc(symbol).file_name,
        func_name=func_name,
        scope_level=scope_level,
        scope_depth=scope_depth,
        ident_name=ident(symbol),
    )


def data_symbol(symbol, bins, symbol_table, func_name='', scope_level=0, scope_depth=0):
    if binaries(symbol):
        symbol_table[name(symbol, func_name, scope_level, scope_depth)] = symbol
        symbol.offset = len(bins)
        bins.append(binaries(symbol))
    elif symbol.storage_class is None:  # Common/Shared
        if name(symbol) in symbol_table:
            assert not symbol_table[name(symbol)].storage_class
            offset = symbol_table[name(symbol)].offset
            symbol = max((symbol, symbol_table.pop(name(symbol))), key=lambda symbol: symbol.size)
            bins[offset] = [Integer(0, loc(symbol))] * symbol.size
        else:
            offset = len(bins)
            bins.append([Integer(0, loc(symbol))] * symbol.size)
        symbol_table[name(symbol)] = symbol
        symbol.offset = offset


def code_symbol(symbol, bins, symbol_table, func_name='', scope_level=0, scope_depth=0):
    if binaries(symbol):
        symbol.offset = len(bins)
        bins.append(())
        symbol_table[name(symbol)] = symbol
        func_name = ident(symbol)
        instrs = []
        for instr in flatten(binaries(symbol)):
            if isinstance(instr, SaveStackPointer):
                scope_level += 1
                scope_depth += 1
            if isinstance(instr, RestoreStackPointer):
                scope_depth -= 1
            if isinstance(instr, Symbol):
                code_symbol.rules[type(instr)](
                    instr, bins, symbol_table, func_name, scope_level, scope_depth
                )
            else:  # remove all symbols.
                instrs.append(instr)
        bins[symbol.offset] = instrs
code_symbol.rules = {
    Data: data_symbol,
    Code: code_symbol,
}


def executable(object_files, entry_point='main'):
    bins = []
    symbol_table = SymbolTable()
    for obj_file in object_files:
        for symbol in obj_file:
            executable.rules[type(symbol)](symbol, bins, symbol_table)
    return BinaryFile(symbol_table, bins, entry_point)
executable.rules = {
    Data: data_symbol,
    Code: code_symbol,
}

