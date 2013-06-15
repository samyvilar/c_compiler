__author__ = 'samyvilar'

from collections import defaultdict

from front_end.loader.locations import loc, LocationNotSet

from front_end.parser.ast.declarations import Declaration, Definition, TypeDef, name, initialization, FunctionDefinition
from front_end.parser.ast.statements import LabelStatement
from front_end.parser.types import c_type, PointerType, VoidType, FunctionType


from back_end.emitter.statements.statement import statement
from back_end.emitter.statements.jump import return_instrs
from back_end.emitter.statements.jump import patch_goto_instrs
from back_end.emitter.object_file import Data, Code
from back_end.emitter.types import binaries, size
from back_end.emitter.instructions.stack_state import stack_allocation, Stack
from back_end.emitter.instructions.data import global_allocation


def no_rule(declarations, *_):
    raise ValueError('{l} No rule to emit binaries for {f}'.format(l=loc(declarations[0]), f=declarations[0]))


def get_directives():
    rules = defaultdict(lambda: no_rule)
    rules.update({
        TypeDef: type_def,
        Declaration: definition,
        Definition: definition,
        FunctionDefinition: function_definition,
    })
    return rules


def type_def(dec, symbol_table):
    symbol_table[name(dec)] = dec


def definition(dec, symbol_table):  # Global definition.
    symbol_type = Code if isinstance(c_type(dec), FunctionType) else Data
    symbol_table[name(dec)] = global_allocation(dec)
    symbol_table[name(dec)].symbol = symbol_type(  # Add reference of symbol to definition to keep track of references
        name(dec),
        binaries(dec),
        size(c_type(dec)),
        dec.storage_class,
        loc(dec),
    )
    return symbol_table[name(dec)].symbol


# Global Function Definition.
def function_definition(dec, symbol_table):
    """
        Function Call Convention:
            Allocate enough space on the stack for the return type at least 1 word, NOTE: void returns 0,
             since function calls are considered expressions, and all expressions leave a value on the stack, hence ...
            Push a new Frame.
            Push the return Address so the callee knows where to return to.
            Push all parameters on the stack from left to right. (The values won't be pop but referenced on stack ...)
            Jump to callee code segment
            callee references values passed on the stack by pushing the base_stack_pointer, pushing the offset value of
            the parameter/declaration in question call Add, then Load.
            Callee will place the return value by Pushing the values,
                Push Stack Pointer, Push size, call Subtract, call Set.
            Caller Pops frame.
    """
    symbol_table[name(dec)] = global_allocation(dec)  # bind load/set/reference instructions, add to symbol table.
    symbol_table[name(dec)].symbol = Code(name(dec), (), size(c_type(dec)), dec.storage_class, loc(dec))
    symbol_table.push_frame()

    stack = Stack()  # Each function call has its own Frame which is nothing more than a stack.
    return_address = PointerType(VoidType(LocationNotSet), LocationNotSet)
    _ = stack_allocation(stack, return_address)  # allocate return address.

    for index, parameter in enumerate(c_type(dec)):
        # monkey patch declarator objects add Load and Set commands according to stack state; add to symbol table.
        symbol_table[name(parameter)] = c_type(dec)[index] = stack_allocation(stack, parameter)

    instrs = [statement(stmnt, symbol_table, stack) for stmnt in dec]
    instrs.extend(return_instrs(instrs and loc(instrs[-1]) or loc(dec)))

    for goto_stmnt in symbol_table.goto_stmnts:
        patch_goto_instrs(goto_stmnt, symbol_table.label_smnts[LabelStatement.get_name(goto_stmnt.label)])

    symbol_table[name(dec)].symbol.binaries = instrs
    _ = symbol_table.pop_frame()

    return symbol_table[name(dec)].symbol