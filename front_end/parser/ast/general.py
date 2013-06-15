__author__ = 'samyvilar'


class Node(object):
    def __init__(self, location):
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
