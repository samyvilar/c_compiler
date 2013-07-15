__author__ = 'samyvilar'

from collections import defaultdict
from itertools import chain

from front_end.loader.locations import loc, LocationNotSet
from front_end.parser.symbol_table import push, pop, SymbolTable

from front_end.parser.ast.statements import FunctionDefinition
from front_end.parser.ast.declarations import Declaration, Definition, name, initialization
from front_end.parser.types import c_type, PointerType, VoidType, FunctionType


from back_end.emitter.statements.statement import statement
from back_end.emitter.statements.jump import return_instrs
from back_end.emitter.object_file import Data, Code
from back_end.emitter.c_types import binaries, size
from back_end.emitter.stack_state import stack_allocation, Stack

from back_end.virtual_machine.instructions.architecture import Address, Push

from back_end.emitter.c_types import bind_load_address_func


def no_rule(dec, *_):
    raise ValueError('{l} No rule to emit binaries for {f}'.format(l=loc(dec), f=dec))


def get_directives():
    rules = defaultdict(lambda: no_rule)
    rules.update({
        Declaration: declaration,
        Definition: definition,
        FunctionDefinition: function_definition,
    })
    return rules


def bind_load_instructions(obj):
    def load_address(self, location):
        yield Push(location, Address(self.symbol, location))

    obj.load_address = bind_load_address_func(load_address, obj)
    return obj


def declaration(dec, symbol_table):
    symbol_table[name(dec)] = bind_load_instructions(dec)
    symbol_table[name(dec)].symbol = Code(name(dec), (), size(c_type(dec)), dec.storage_class, loc(dec)) \
        if isinstance(c_type(dec), FunctionType) \
        else Data(name(dec), (), size(c_type(dec)), dec.storage_class, loc(dec))
    return symbol_table[name(dec)].symbol


def definition(dec, symbol_table):  # Global definition.
    assert not isinstance(c_type(dec), FunctionType)
    symbol_table[name(dec)] = bind_load_instructions(dec)
    symbol_table[name(dec)].symbol = Data(  # Add reference of symbol to definition to keep track of references
        name(dec), binaries(dec), size(c_type(dec)), dec.storage_class, loc(dec),
    )
    return symbol_table[name(dec)].symbol


# Global Function Definition.
def function_definition(dec, symbol_table):
    """
    Function Call Convention:
        Allocate enough space on the stack for the return type.
        Push a new Frame (saves (base & stack ptr) then resets the base_stack pointer to the current stack pointer)
        Push the return Address so the callee knows where to return to.
        Push all parameters on the stack from left to right. (The values won't be pop but referenced on stack ...)
        Jump to callee code segment
        callee references values passed on the stack by pushing the base_stack_pointer, pushing the offset of
        the parameter/declaration in question call Add, then Load.
        Callee will place the return value using the base stack pointer and opposite addressing arithmetic.
        Caller Pops frame, and uses the set value.
    """
    symbol = Code(name(dec), None, size(c_type(dec)), dec.storage_class, loc(dec))
    symbol_table[name(dec)] = bind_load_instructions(dec)  # bind load/reference instructions, add to symbol table.
    symbol_table[name(dec)].symbol = symbol

    def binaries(body, symbol_table):
        symbol_table = push(symbol_table)
        stack = Stack()  # Each function call has its own Frame which is nothing more than a stack.

        _ = stack_allocation(stack, PointerType(VoidType(LocationNotSet), LocationNotSet))  # allocate return address.
        for index, parameter in enumerate(c_type(dec)):
            # monkey patch declarator objects add Load commands according to stack state; add to symbol table.
            symbol_table[name(parameter)] = c_type(dec)[index] = stack_allocation(stack, parameter)

        symbol_table['__ CURRENT FUNCTION __'] = dec
        symbol_table['__ LABELS __'] = SymbolTable()
        symbol_table['__ GOTOS __'] = defaultdict(list)
        for instr in chain(
                chain.from_iterable(statement(s, symbol_table, stack) for s in chain.from_iterable(body)),
                return_instrs(loc(dec))
        ):
            yield instr
        _ = pop(symbol_table)

    symbol.binaries = binaries(initialization(dec), symbol_table)
    return symbol