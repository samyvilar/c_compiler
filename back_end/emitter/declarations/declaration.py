__author__ = 'samyvilar'

from types import MethodType
from collections import defaultdict
from itertools import chain, imap, repeat, izip

from front_end.loader.locations import loc
from utils.symbol_table import push, pop, SymbolTable

from front_end.parser.ast.statements import FunctionDefinition
from front_end.parser.ast.declarations import Declaration, Definition, name, initialization
from front_end.parser.types import c_type, void_pointer_type, FunctionType, VoidType, ArrayType


from back_end.emitter.statements.jump import return_instrs
from back_end.emitter.object_file import Data, Code, Reference
from back_end.emitter.c_types import size, size_arrays_as_pointers
from back_end.emitter.stack_state import Stack, bind_instructions

from back_end.virtual_machine.instructions.architecture import Address, push as push_instr, Pass

from back_end.emitter.expressions.static import static_def_binaries, bind_load_address_func


def no_rule(dec, *_):
    raise ValueError('{l} No rule to emit binaries for {f}'.format(l=loc(dec), f=dec))


def get_directives():
    return defaultdict(
        lambda: no_rule,
        ((Declaration, declaration), (Definition, definition), (FunctionDefinition, function_definition))
    )


def bind_load_instructions(obj):
    def load_address(self, location):
        return push_instr(self.get_address_obj(location), location)

    def get_address_obj(self, location):
        return Address(Reference(self.symbol.name), location)

    obj.get_address_obj = MethodType(get_address_obj, obj)
    obj.load_address = bind_load_address_func(load_address, obj)
    return obj


def declaration(dec, symbol_table):
    symbol_table[name(dec)] = bind_load_instructions(dec)
    symbol_table[name(dec)].symbol = Code(name(dec), (), None, dec.storage_class, loc(dec)) \
        if isinstance(c_type(dec), FunctionType) \
        else Data(name(dec), (), size(c_type(dec)), dec.storage_class, loc(dec))
    return symbol_table[name(dec)].symbol


def definition(dec, symbol_table):  # Global definition.
    assert not isinstance(c_type(dec), FunctionType)
    symbol_table[name(dec)] = bind_load_instructions(dec)
    symbol_table[name(dec)].symbol = Data(  # Add reference of symbol to definition to keep track of references
        # static binaries, (packed binaries since machine may require alignment ...)
        name(dec), static_def_binaries(dec), size(c_type(dec)), dec.storage_class, loc(dec),
    )
    return symbol_table[name(dec)].symbol


# Global Function Definition.
def function_definition(dec, symbol_table):
    """
    Function Call Convention:
        Allocate enough space on the stack for the return type.

        Push a new Frame (saves (base & stack ptr))
        Push all parameters on the stack from right to left. (The values won't be pop but referenced on stack (+) ...)
        Calculate & Push pointer where to return value.

        Push pointer where to store return value.
        Push the return Address so the callee knows where to return to.
        (Reset Base pointer) creating a new Frame.
        Jump to callee code segment

        callee references values passed on the stack by pushing the base_stack_pointer,
        (+offsets) for previous frame and (-offset) for current frame ...

        Callee will place the return value in the specified pointer.
        Caller Pops frame, and uses the set (returned) value.
    """
    symbol = Code(name(dec), None, None, dec.storage_class, loc(dec))
    symbol_table[name(dec)] = bind_load_instructions(dec)  # bind load/reference instructions, add to symbol table.
    symbol_table[name(dec)].symbol = symbol

    def binaries(body, symbol_table):
        symbol_table = push(symbol_table)
        symbol_table['__ stack __'] = Stack()  # Each function call has its own Frame which is nothing more than a stack

        # Skip return address ...
        offset = size_arrays_as_pointers(void_pointer_type) + (
            # if function has zero return size then the return pointer will be omitted ...
            size_arrays_as_pointers(void_pointer_type) *
            bool(size_arrays_as_pointers(c_type(c_type(dec)), overrides={VoidType: 0}))
        )

        for parameter in c_type(dec):
            # monkey patch declarator objects add Load commands according to stack state; add to symbol table.
            symbol_table[name(parameter)] = bind_instructions(parameter, offset)
            assert not type(parameter) is ArrayType  # TODO: fix this.
            offset += size_arrays_as_pointers(c_type(parameter))

        symbol_table.update(
            izip(('__ CURRENT FUNCTION __', '__ LABELS __', '__ GOTOS __'), (dec, SymbolTable(), defaultdict(list)))
        )

        def pop_symbol_table(symbol_table, location=loc(dec)):  # pop symbol table once all binaries have being emitted
            yield (pop(symbol_table) or 1) and Pass(location)

        return chain(   # body of function ...
            chain.from_iterable(imap(symbol_table['__ statement __'], chain.from_iterable(body), repeat(symbol_table))),
            return_instrs(loc(dec)),        # default return instructions, in case one was not giving ...
            pop_symbol_table(symbol_table)  # pop symbol_table once complete ...
        )

    symbol.binaries = binaries(initialization(dec), symbol_table)
    return symbol