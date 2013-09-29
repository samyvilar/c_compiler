__author__ = 'samyvilar'


from collections import defaultdict

from back_end.virtual_machine.instructions.architecture import ids, instr_objs, Pass, Halt
from back_end.virtual_machine.instructions.architecture import VariableLengthInstruction, WideInstruction, Instruction

from back_end.virtual_machine.instructions.stack import stack_instrs
from back_end.virtual_machine.instructions.expressions.binary import binary_instrs
from back_end.virtual_machine.instructions.expressions.unary import unary_instrs

from back_end.virtual_machine.instructions.flags import load_flag_instrs
from back_end.virtual_machine.instructions.jump import jump_instrs

from back_end.virtual_machine.operands import oprn

from back_end.virtual_machine.cpu.word import Word


class HaltException(Exception):
    pass


def invalid_instruction(instr, cpu, mem):
    raise ValueError('Invalid instruction {instr}'.format(instr=instr))


def halt(*_):
    raise HaltException()


def no_operand_instrs(instr, cpu, mem):
    no_operand_instrs.rules[instr](instr, cpu, mem)
    cpu.instr_pointer += cpu.word_type(instr_size(instr))


def single_operand_instr(instr, cpu, mem):
    single_operand_instr.rules[instr](instr, cpu, mem)
    cpu.instr_pointer += cpu.word_type(instr_size(instr)) + cpu.word_type(operand_size(oprn(cpu, mem)))


def variable_length_instr(instr, cpu, mem):
    variable_length_instr.rules[instr](instr, cpu, mem)
    cpu.instr_pointer += cpu.word_type(instr_size(instr)) + cpu.word_type(oprn(cpu, mem))


def get_directives():
    variable_length_instr.rules = {  # Variable length instructions (JumpTable)
        instr_id: get_directives.rules[instr_id]
        for instr_id in get_directives.rules
        if issubclass(instr_objs[instr_id], VariableLengthInstruction)
    }

    single_operand_instr.rules = {  # Single operand instructions Push, Jump, Load, Set
        instr_id: get_directives.rules[instr_id]
        for instr_id in set(get_directives.rules) - set(variable_length_instr.rules)
        if issubclass(instr_objs[instr_id], WideInstruction)
    }

    no_operand_instrs.rules = {  # Arithmetic instrs, Add, Sub, ... Pop
        instr_id: get_directives.rules[instr_id]
        for instr_id in set(get_directives.rules) - set(variable_length_instr.rules) - set(single_operand_instr.rules)
        if issubclass(instr_objs[instr_id], Instruction)
    }

    assert set(no_operand_instrs.rules) | set(single_operand_instr.rules) | set(variable_length_instr.rules) == set(
        get_directives.rules
    )

    rules = defaultdict(lambda: invalid_instruction)
    rules.update({rule: no_operand_instrs for rule in no_operand_instrs.rules})
    rules.update({rule: single_operand_instr for rule in single_operand_instr.rules})
    rules.update({rule: variable_length_instr for rule in variable_length_instr.rules})

    # override instr pointer update for jump instructions, since they may modify it
    rules.update({rule: jump_instrs for rule in jump_instrs.rules})
    return rules
get_directives.rules = {ids[Pass]: lambda *_: None, ids[Halt]: halt}
get_directives.rules.update({rule: binary_instrs for rule in binary_instrs.rules})
get_directives.rules.update({rule: unary_instrs for rule in unary_instrs.rules})
get_directives.rules.update({rule: load_flag_instrs for rule in load_flag_instrs.rules})
get_directives.rules.update({rule: stack_instrs for rule in stack_instrs.rules})
get_directives.rules.update({rule: jump_instrs for rule in jump_instrs.rules})


class CPU(defaultdict):
    def __init__(self, instr_pointer=None, instr_set=get_directives(), word_type=Word):
        self.word_type = word_type
        self.carry, self.overflow, self.zero = word_type(0), word_type(0), word_type(0)
        self.base_stack_pointer = self.stack_pointer = word_type(-1)
        self.instr_pointer = instr_pointer or word_type(0)
        super(CPU, self).__init__(instr_set.default_factory, instr_set)


def instr_size(*args):
    return 1


def operand_size(*args):
    return 1