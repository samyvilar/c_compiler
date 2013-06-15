__author__ = 'samyvilar'


class List(list):
    def __init__(self, seq=()):
        self.consumed = []
        super(List, self).__init__(seq)

    def pop(self, index=None):
        self.consumed.append(super(List, self).pop(index))
        return self.consumed[-1]

    def extend(self, iterable):
        for p_object in iterable:
            self.append(p_object)


def consumed(obj):
    return getattr(obj, 'consumed', [])