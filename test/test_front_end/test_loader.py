__author__ = 'samyvilar'

from unittest import TestCase

from front_end.loader.load import source
from front_end.loader.locations import loc


class LoaderTest(TestCase):
    def test_get_lines(self):
        test_input = """
this is a new lines
this is \\
supposed to \\
be a new line \\
also. ... \\
empty.
"""
        new_char_array = source(test_input, '__TEST__')
        self.assertEqual(''.join(new_char_array),
                         '\nthis is a new lines\nthis is supposed to be a new line also. ... empty.\n')
        locations = \
            [('__TEST__', 1, 1)] + [
                ('__TEST__', 2, index)
                for index, ch in enumerate('this is a new lines\n', 1)
            ] + [
                ('__TEST__', 3, index)
                for index, ch in enumerate('this is supposed to be a new line also. ... empty.\n', 1)
            ]

        for index, ch in enumerate(new_char_array):
            self.assertEqual(loc(ch), locations[index])