__author__ = 'samyvilar'

import os

from itertools import chain, ifilter, ifilterfalse, imap, product

try:
    import cPickle as pickle
except ImportError as _:
    import pickle

from front_end.loader.locations import loc
from front_end.parser.symbol_table import SymbolTable
from back_end.emitter.object_file import Data, Reference, Symbol
from back_end.emitter.c_types import size

from front_end.parser.types import VoidPointer

from front_end.tokenizer.tokens import IDENTIFIER
from front_end.parser.ast.expressions import FunctionCallExpression, AssignmentExpression, IdentifierExpression

from back_end.emitter.expressions.expression import expression

from back_end.virtual_machine.instructions.architecture import Push, PushFrame, PopFrame, Halt, Integer, Allocate, Set
from back_end.virtual_machine.instructions.architecture import RelativeJump, Pass, Address, operns, Byte
from back_end.virtual_machine.instructions.architecture import LoadStackPointer, SetBaseStackPointer, Add


def insert(symbol, symbol_table):
    if symbol.binaries:  # definition
        symbol_table[symbol.name] = symbol
    else:
        if isinstance(symbol, Data) and not symbol.storage_class:  # declaration.
            # C coalesces multiple declarations across multiple files as long as they don't have a storage class
            if symbol.name in symbol_table:  # only keep largest.
                if symbol.size > symbol_table[symbol.name].size:
                    _ = symbol_table.pop(symbol.name)
                    symbol_table[symbol.name] = symbol
            else:
                symbol_table[symbol.name] = symbol


def static(instrs, symbol_table=None, library_dirs=(), libraries=()):
    symbol_table = symbol_table or SymbolTable()
    references = {}
    for instr in instrs:
        for o in operns(instr):
            if isinstance(getattr(o, 'obj', None), Reference):
                references[o.obj.name] = o
        yield instr

    instrs = None
    for ref_name in ifilter(lambda n, table=symbol_table: n not in table, references.iterkeys()):
        for lib_file in ifilter(os.path.isfile, imap(lambda p: os.path.join(*p), product(library_dirs, libraries))):
            with open(lib_file) as file_obj:
                lib_symbol_table = pickle.load(file_obj)
                if ref_name in lib_symbol_table:
                    instrs = static(
                        binaries(lib_symbol_table[ref_name], symbol_table), symbol_table, library_dirs, libraries
                    )
                    break
        if instrs is None:
            raise ValueError('{l} Could no locate symbol {s}'.format(l=loc(references[ref_name]), s=ref_name))

    for instr in instrs or ():
        yield instr


def shared(instrs, symbol_table=None, library_dirs=(), libraries=()):
    pass


def library(symbols, symbol_table=None):
    symbol_table = symbol_table or SymbolTable()
    for symbol in symbols:
        insert(symbol, symbol_table)
        symbol.binaries = tuple(symbol.binaries)
    return symbol_table


def binaries(symbol, symbol_table):
    insert(symbol, symbol_table)
    for index, instr in enumerate(symbol.binaries):
        if index == 0:
            symbol.first_element = instr
        yield instr


def set_binaries(symbol):
    assert not symbol.binaries and isinstance(symbol, Data)
    symbol.first_element = Byte(0, loc(symbol))
    symbol.binaries = chain((symbol.first_element,), (Byte(0, loc(symbol)) for _ in xrange(symbol.size - 1)))
    return symbol.binaries


def executable(symbols, symbol_table=None, entry_point='main', library_dirs=(), libraries=(), linker=static):
    symbol_table = symbol_table if symbol_table is not None else SymbolTable()
    location = '__SOP__'  # Start of Program
    clean = Pass(location)
    heap_ptr = Byte(0, location)

    symbols = chain(
        symbols,
        (Data('__heap_ptr__', (Address(0, location),), size(VoidPointer), None, location),)
    )

    def symbol_binaries(symbols, symbol_table):
        for instr in chain.from_iterable(binaries(symbol, symbol_table) for symbol in symbols):
            yield instr
        for value in chain.from_iterable(imap(set_binaries,
                                              ifilterfalse(lambda symbol: symbol.binaries, symbol_table.itervalues()))):
            yield value

    return linker(
        chain(
            (   # Initialize heap pointer ...
                Push(location, Address(heap_ptr, location)),
                Push(location, Address(Reference('__heap_ptr__'), location)),
                Set(location, size(VoidPointer)),
                Allocate(location, -1 * size(VoidPointer)),

                Push(location, Integer(0, location)),  # return value
                PushFrame(location),
                # Add parameters ...

                # Add pointer to return values
                LoadStackPointer(location),
                Push(location, Integer(1, location)),
                Add(location),

                Push(location, Address(clean, location)),  # clean up after main exits
                LoadStackPointer(location),
                SetBaseStackPointer(location),
                RelativeJump(location, Address(Reference(entry_point))),  # jump to main
            ),
            symbol_binaries(symbols, symbol_table),
            (
                clean,
                PopFrame(location),
                Allocate(location, -1 * size(Integer(0, location))),
                Halt(location),
                heap_ptr
            )
        ),
        symbol_table,
        library_dirs,
        libraries,
    )


def resolve(instrs, symbol_table):
    references = []
    for instr in instrs:
        for o in operns(instr):
            if isinstance(getattr(o, 'obj', None), Reference):
                references.append(o)
        yield instr

    for operand in references:
        symbol = symbol_table[operand.obj.name]
        if hasattr(symbol, 'first_element'):
            operand.obj = symbol.first_element
        else:
            raise ValueError('{l} Unable to resolve symbol {s}'.format(l=loc(symbol), s=symbol))