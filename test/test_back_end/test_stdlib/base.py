__author__ = 'samyvilar'

from unittest import TestCase
from StringIO import StringIO

from c_comp import instrs, std_include_dirs, std_libraries_dirs, std_libraries

from collections import defaultdict
from back_end.emitter.cpu import load, evaluate, CPU


class TestStdLib(TestCase):
    def evaluate(self, code):
        self.cpu, self.mem = CPU(), defaultdict(int)
        load(instrs((StringIO(code),), std_include_dirs, std_libraries_dirs, std_libraries), self.mem)
        evaluate(self.cpu, self.mem)
