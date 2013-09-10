__author__ = 'samyvilar'

from unittest import TestCase
from itertools import izip, chain
from collections import defaultdict
from back_end.virtual_machine.cpu.core import CPU

import back_end.virtual_machine.instructions.encoder as encoder
from back_end.virtual_machine.instructions.architecture import Push, Pop, Halt, Load
from back_end.virtual_machine.instructions.architecture import ids, LoadBaseStackPointer, LoadStackPointer, Add
from back_end.virtual_machine.instructions.stack import _push, _pop
from back_end.virtual_machine.cpu.core import HaltException


def size(value):
    return 1


def encode(instrs, word_type):
    return {
        addr: instr for addr, instr in izip(
            encoder.addresses(word_type(1), word_type(1)), encoder.encode(instrs, word_type)
        )
    }


class TestCPU(TestCase):
    def setUp(self):
        self.cpu = CPU()
        self.mem = defaultdict(self.cpu.word_type)

    def execute(self, instrs):
        self.mem.update(encode(chain.from_iterable(chain(instrs, (Halt('__EOP__'),))), self.cpu.word_type))

        while True:
            instr = self.mem[self.cpu.instr_pointer]
            if int(instr) == ids[Halt]:
                self.assertRaises(HaltException, lambda: self.cpu[instr](instr, self.cpu, self.mem))
                break
            self.cpu[instr](instr, self.cpu, self.mem)


class TestCPUStack(TestCPU):
    def test_push(self):
        value = 5
        original_stack_pointer = self.cpu.stack_pointer
        self.execute((Push('', value),))
        self.assertLess(int(self.cpu.stack_pointer), int(original_stack_pointer))
        self.assertEqual(_pop(self.cpu, self.mem), value)
        self.assertEqual(self.cpu.stack_pointer, original_stack_pointer)

    def test_pop(self):
        value = -1
        original_stack_pointer = self.cpu.stack_pointer
        self.execute((Push('', value), Pop('')))
        self.assertEqual(self.cpu.stack_pointer, original_stack_pointer)
        _push(value, self.cpu, self.mem)
        self.assertEqual(_pop(self.cpu, self.mem), value)

    def test_load_base_stack_pointer(self):
        self.cpu.base_stack_pointer = -1
        self.execute((LoadBaseStackPointer(''),))
        self.assertEqual(_pop(self.cpu, self.mem), self.cpu.base_stack_pointer)

    def test_load_stack_pointer(self):
        stack_pointer = self.cpu.stack_pointer
        self.execute((LoadStackPointer(''),))
        self.assertEqual(_pop(self.cpu, self.mem), stack_pointer)

    def test_load(self):
        values = [4, 5, 8]
        stack_pointer = self.cpu.stack_pointer
        self.execute(
            chain(
                (Push('', v) for v in values),
                (LoadStackPointer(''), Push('', 1), Add(''), Load('', len(values) * size(values[0])))
            )
        )
        for addr, val in sorted(encode(chain(values, reversed(values)),
                                       self.cpu.word_type).iteritems(), key=lambda v: int(v[0])):
            self.assertEqual(_pop(self.cpu, self.mem), val)
        self.assertEqual(self.cpu.stack_pointer, stack_pointer)