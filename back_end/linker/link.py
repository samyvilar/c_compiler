__author__ = 'samyvilar'

import os

from itertools import chain, ifilter, ifilterfalse, imap, product, starmap, izip, repeat

try:
    import cPickle as pickle
except ImportError as _:
    import pickle

from front_end.loader.locations import loc
from front_end.parser.symbol_table import SymbolTable
from back_end.emitter.object_file import Data, Reference
from back_end.emitter.c_types import size

from front_end.parser.types import void_pointer_type

from back_end.virtual_machine.instructions.architecture import Push, Halt, Set
from back_end.virtual_machine.instructions.architecture import Address, operns, Byte, allocate


from back_end.emitter.declarations.declaration import declaration
from back_end.emitter.statements.statement import statement
from front_end.parser.ast.declarations import Declaration, name
from front_end.parser.ast.expressions import FunctionCallExpression, IdentifierExpression
from front_end.parser.types import IntegerType, FunctionType, c_type


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


def static(instrs, symbol_table=None, libraries=()):
    symbol_table = SymbolTable() if symbol_table is None else symbol_table
    references = {}
    for instr in instrs:
        for o in operns(instr):
            if isinstance(getattr(o, 'obj', None), Reference):
                references[o.obj.name] = o
        yield instr

    for ref_name in ifilterfalse(lambda n, table=symbol_table: n in table, references.iterkeys()):
        try:
            l = next(ifilter(lambda lib, ref_name=ref_name: ref_name in lib, libraries))
            for instr in static(binaries(l[ref_name], symbol_table), symbol_table, libraries):
                yield instr
        except StopIteration as _:
            raise ValueError('{l} Could no locate symbol {s}'.format(l=loc(references[ref_name]), s=ref_name))


def shared(instrs, symbol_table=None, libraries=()):
    raise NotImplementedError


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


class Library(object):
    # Cached library object will load and maintain a copy of the library only when __contains__ or __getitem__ r called
    def __init__(self, path):
        self.path = path
        self._source = None

    def __contains__(self, item):
        return item in self.source

    def __getitem__(self, item):
        return self.source[item]

    @property
    def source(self):
        return self._source or self._load()

    def _load(self):
        with open(self.path, 'rb') as file_obj:
            self._source = pickle.load(file_obj)
        return self._source


def executable(
        symbols,
        symbol_table=None,
        entry_point=Declaration('main', FunctionType(IntegerType())),
        library_dirs=(),
        libraries=(),
        linker=static):
    symbol_table = SymbolTable() if symbol_table is None else symbol_table
    location = '__SOP__'  # Start of Program
    heap_ptr = Byte(0, location)

    libs = tuple(
        Library(lib_file)
        for lib_file in ifilter(os.path.isfile, starmap(os.path.join, product(library_dirs, libraries)))
    )
    symbols = chain(
        symbols,
        (Data('__heap_ptr__', (Address(0, location),), size(void_pointer_type), None, location),)
    )

    def declarations(symbol_table):
        for v in chain.from_iterable(imap(set_binaries, ifilterfalse(lambda s: s.binaries, symbol_table.itervalues()))):
            yield v   # declarations ....

    st = {}
    _ = declaration(entry_point, st)
    instr_seq = chain(
        (   # Initialize heap pointer ...
            Push(location, Address(heap_ptr, location)),
            Push(location, Address(Reference('__heap_ptr__'), location)),
            Set(location, size(void_pointer_type)),
        ),
        allocate(Address(-1 * size(void_pointer_type), location)),
        statement(  # call entry point ...
            FunctionCallExpression(
                IdentifierExpression(name(entry_point), c_type(entry_point), location),
                (),
                c_type(c_type(entry_point)),
                location
            ),
            st
        ),
        (Halt(location),),
        chain.from_iterable(starmap(binaries, izip(symbols, repeat(symbol_table))))
    )
    return chain(linker(instr_seq, symbol_table, libs), declarations(symbol_table), (heap_ptr,))


def resolve(instrs, symbol_table):
    references = []
    for instr in instrs:
        for o in operns(instr):
            if isinstance(getattr(o, 'obj', None), Reference):
                references.append(o)
        yield instr

    for operand in references:
        symbol = symbol_table[operand.obj.name]
        if not hasattr(symbol, 'first_element'):
            raise ValueError('{l} Unable to resolve symbol {s}'.format(l=loc(symbol), s=symbol))
        operand.obj = symbol.first_element