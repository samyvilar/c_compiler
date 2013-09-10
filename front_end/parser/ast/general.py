__author__ = 'samyvilar'

from front_end.loader.locations import LocationNotSet


class Node(object):
    def __init__(self, location=LocationNotSet):
        self.location = location

    def __eq__(self, other):
        return type(other) is type(self)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __nonzero__(self):
        return 1


class EmptyNode(Node):
    def __nonzero__(self):
        return 0
