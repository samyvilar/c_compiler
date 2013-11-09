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

from back_end.virtual_machine.instructions.architecture import halt, Byte, Double, Instruction
from back_end.virtual_machine.instructions.architecture import Address, Offset, operns, RelativeJump, Integer

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
        linker=static
):
    symbol_table = SymbolTable() if symbol_table is None else symbol_table
    location = '__SOP__'  # Start of Program
    __end__ = Integer(0, location)

    libs = tuple(
        Library(lib_file)
        for lib_file in ifilter(os.path.isfile, starmap(os.path.join, product(library_dirs, libraries)))
    )
    symbols = chain(
        symbols,  # add heap pointer(s) ...
        (
            Data('__base_heap_ptr__', (Address(__end__, location),), size(void_pointer_type), None, location),
            Data('__heap_ptr__', (Address(__end__, location),), size(void_pointer_type), None, location),
        )
    )

    def declarations(symbol_table):
        for v in chain.from_iterable(imap(set_binaries, ifilterfalse(lambda s: s.binaries, symbol_table.itervalues()))):
            yield v   # declarations ....

    st = {}
    _ = declaration(entry_point, st)
    instr_seq = chain(
        statement(  # call entry point ...
            FunctionCallExpression(
                IdentifierExpression(name(entry_point), c_type(entry_point), location),
                (),
                c_type(c_type(entry_point)),
                location
            ),
            st
        ),
        halt(location),  # Halt machine on return ...
        chain.from_iterable(starmap(binaries, izip(symbols, repeat(symbol_table)))),
    )            # link all foreign symbols and emit binaries for declarations ...
    return chain(linker(instr_seq, symbol_table, libs), declarations(symbol_table), (__end__,))


def resolve(instrs, symbol_table):
    # resolve all references ... replace Address(obj=Reference(symbol_name)) by Address(obj=instr)
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


def set_addresses(instrs, addresses=None):  # assign addresses ...
    def default_address_gen():
        previous_address = 0
        _ = (yield)
        while True:
            _ = (yield previous_address)  # TODO: calculate address based on size of previous instr (for now all 1)
            previous_address += 1

    addresses = addresses or default_address_gen()
    _ = next(addresses)
    references = []

    for instr in instrs:
        instr.address = addresses.send(instr)  # calculate next address based on current value ...
        yield instr

        if type(instr) is Address and type(instr.obj) not in {int, long}:
            references.append((instr, instr, None))

        for operand_index, o in enumerate(operns(instr)):
            if isinstance(o, (Address, Offset)) and type(o.obj) not in {int, long}:
                references.append((instr, o, operand_index))

            # replace immutable int type by mutable type.
            if type(o) in {int, long}:
                o = Integer(o, loc(instr))
                instr[operand_index] = o
            elif type(o) is float:
                o = Double(o, loc(instr))
                instr[operand_index] = o  # update instruction operand.

            o.address = addresses.send(o)

                # if not isinstance(o.obj, (int, long)):  # referencing a symbol that has yet to be resolved ...
                #     symbol_references.append((instr, o, operand_index))
                # elif isinstance(o.obj, NoneType):  # referencing an unseen label ...
                #     label_references.append((instr, o, operand_index))
                # elif isinstance(o.obj, (Instruction, Operand)):  # referencing an instr or Operand..
                #     instr_references.append((instr, o, operand_index))
                # elif not isinstance(o.obj, (int, long)):
                #     raise ValueError('Bad operand type {t} for Address object ...'.format(t=type(o.obj)))
            yield o

    # At this point all address have being generated and resolve() should have checked or set first_element on Refs ...
    # so update addresses replace Address(obj=instr) by Address(obj=address or offset)

    for instr, operand, operand_index in references:
        if isinstance(operand, Offset):
            operand.obj = operand.obj.address - ((instr.address + 2) if isinstance(instr, RelativeJump) else 0)
        else:
            operand.obj = operand.obj.address

        # Update instruction operand ...
        if isinstance(instr, Instruction):
            instr[operand_index] = Address(operand.obj, loc(operand))


