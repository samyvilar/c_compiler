__author__ = 'samyvilar'

from logging_config import logging
from back_end.virtual_machine.memory import VirtualMemory
from back_end.virtual_machine.cpu.core import CPU, HaltException

logger = logging.getLogger('virtual_machine')


class VirtualMachine(object):
    def __init__(self, memory=None, cpu=None):
        self.memory, self.cpu = memory or VirtualMemory(), cpu or CPU()

    def start(self):
        while True:
            instr = self.memory[self.cpu.instr_pointer]
            try:
                self.cpu[instr](instr, self.cpu, self.memory)
            except HaltException as ex:
                logger.info('Virtual Machine halted.')
                break
