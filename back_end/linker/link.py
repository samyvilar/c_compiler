__author__ = 'samyvilar'

from itertools import chain, ifilter, ifilterfalse, imap, starmap, izip, repeat
from back_end.emitter.cpu import word_size

try:
    import cPickle as pickle
except ImportError as _:
    import pickle

from front_end.loader.locations import loc
from utils.symbol_table import SymbolTable
import back_end.emitter.object_file as object_file
from back_end.emitter.c_types import size

from front_end.parser.types import void_pointer_type

from back_end.virtual_machine.instructions.architecture import halt, Byte, Double, Instruction, referenced_obj
from back_end.virtual_machine.instructions.architecture import Address, Offset, operns, RelativeJump, Word, Pass

from back_end.emitter.declarations.declaration import declaration
from back_end.emitter.statements.statement import statement
from back_end.emitter.expressions.expression import expression

from front_end.parser.ast.declarations import Declaration, name, Extern

from front_end.parser.ast.expressions import FunctionCallExpression, IdentifierExpression
from front_end.parser.types import IntegerType, FunctionType, c_type


def insert_definition(symbol, symbol_table):
    _ = symbol.name in symbol_table and not symbol.binaries and isinstance(symbol_table[symbol.name], object_file.Data)\
        and symbol_table.pop(symbol.name)  # replace data declaration by definition
    symbol_table[symbol.name] = symbol


def insert_declaration(symbol, symbol_table):  # declarations ...
    if isinstance(symbol, object_file.Data) and not isinstance(symbol.storage_class, Extern):
        # insert non-extern declarations
        if symbol.name not in symbol_table:
            symbol_table[symbol.name] = symbol
        else:  # C coalesces multiple declarations across multiple files ...
            if symbol.size >= symbol_table[symbol.name].size:  # insert largest declaration ...
                symbol_table[symbol.name] = (symbol_table.pop(symbol.name) or 1) and symbol
    # Don't insert Code declarations unless they have have being defined (it has binaries)...


def insert(symbol, symbol_table):  # insert definition if it has any binaries else insert as declaration ...
    ((symbol.binaries and insert_definition) or insert_declaration)(symbol, symbol_table)


def static(instrs, symbol_table=None, libraries=()):
    symbol_table = SymbolTable() if symbol_table is None else symbol_table
    references = {}
    for instr in instrs:
        for o in operns(instr, ()):
            if isinstance(referenced_obj(o, None), object_file.Reference):
                references[referenced_obj(o).name] = o
        yield instr

    for ref_name in ifilterfalse(symbol_table.__contains__, references.iterkeys()):
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

terminal = object()


def binaries(symbol, symbol_table):
    insert(symbol, symbol_table)
    bins = iter(symbol.binaries)
    first_element = next(bins, terminal)
    if first_element is not terminal:
        symbol.first_element = first_element
        yield first_element
        for instr in bins:
            yield instr


def set_binaries(symbol):
    assert not symbol.binaries and isinstance(symbol, object_file.Data)
    instrs = starmap(Byte, repeat((0, loc(symbol)), symbol.size))
    first_instr = next(instrs, terminal)
    symbol.first_element = Pass(loc(symbol)) if first_instr is terminal else first_instr  # zero sized decl use Pass
    symbol.binaries = chain((symbol.first_element,), instrs)
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


default_entry_point = Declaration('main', FunctionType(IntegerType()))


def executable(symbols, symbol_table=None, entry_point=default_entry_point, libraries=(), linker=static):
    location = '__SOP__'  # Start of Program
    symbol_table = SymbolTable() if symbol_table is None else symbol_table
    __end__ = Word(0, location)
    libs = tuple(imap(Library, libraries))

    symbols = chain(
        symbols,  # add heap pointer(s) ...
        (
            object_file.Data(
                '__base_heap_ptr__', (Address(__end__, location),), size(void_pointer_type), None, location
            ),
            object_file.Data(
                '__heap_ptr__', (Address(__end__, location),), size(void_pointer_type), None, location
            ),
        )
    )

    def declarations(symbol_table):
        # iterate over all symbols withing symbol_table that do not have binaries (they should be declarations)
        for v in chain.from_iterable(imap(set_binaries, ifilterfalse(lambda s: s.binaries, symbol_table.itervalues()))):
            yield v   # emit default binaries for declarations ...

    # inject declaration into temp symbol_table to generate entry point function call instructions ...
    st = {'__ expression __': expression}
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
        references.extend(
            ifilter(lambda o: isinstance(referenced_obj(o, None), object_file.Reference), operns(instr, ()))
        )
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
        while True:  # TODO: calculate address based on size of previous instr (for now all 1 word)
            _ = (yield previous_address)
            previous_address += word_size

    addresses = addresses or default_address_gen()
    _ = next(addresses)
    references = []

    for instr in instrs:
        instr.address = addresses.send(instr)  # calculate next address based on current value ...
        yield instr

        if type(instr) is Address and type(instr.obj) not in {int, long}:
            references.append((instr, instr, None))

        for operand_index, o in enumerate(operns(instr, ())):
            if isinstance(o, (Address, Offset)) and type(o.obj) not in {int, long}:
                references.append((instr, o, operand_index))

            # replace immutable int type by mutable type.
            if type(o) in {int, long}:
                o = Word(o, loc(instr))
                instr[operand_index] = o
            elif type(o) is float:
                o = Double(o, loc(instr))
                instr[operand_index] = o  # update instruction operand.

            o.address = addresses.send(o)
            yield o

    # At this point all address have being generated and resolve() should have checked or set first_element on Refs ...
    # so update addresses replace Address(obj=instr) by Address(obj=address or offset)
    # print '\n'.join(imap(str, references))
    for instr, operand, operand_index in references:
        if not hasattr(operand.obj, 'address'):
            print instr, loc(operand), '  no_address ---> ', id(operand.obj), operand.obj
        if isinstance(operand, Offset):
            operand.obj = operand.obj.address - (
                instr.address + (2 * word_size if isinstance(instr, RelativeJump) else 0)
            )
        else:
            operand.obj = operand.obj.address

        # Update instruction operand ...
        if isinstance(instr, Instruction):
            instr[operand_index] = operand.__class__(operand.obj, loc(operand))


