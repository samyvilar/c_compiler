__author__ = 'samyvilar'

from unittest import TestCase
from StringIO import StringIO

from c_comp import instrs, std_include_dirs, std_libraries_dirs, std_libraries

from collections import defaultdict
from back_end.emitter.cpu import load, evaluate, CPU, Kernel
from back_end.emitter.system_calls import CALLS


class TestStdLib(TestCase):
    def evaluate(self, code, cpu=None, mem=None, os=None):
        self.cpu, self.mem, self.os = cpu or CPU(), mem or defaultdict(int), Kernel(CALLS)
        load(instrs((StringIO(code),), std_include_dirs, std_libraries_dirs, std_libraries), self.mem)
        evaluate(self.cpu, self.mem, self.os)