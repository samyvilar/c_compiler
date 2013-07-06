__author__ = 'samyvilar'


class Location(tuple):  # we want locations to be immutable.
    __slots__ = []

    # noinspection PyInitNewSignature
    def __new__(cls, file_name, line_number, column_number):
        return tuple.__new__(cls, (file_name, line_number, column_number))

    @property
    def file_name(self):
        return tuple.__getitem__(self, 0)

    @property
    def line_number(self):
        return tuple.__getitem__(self, 1)

    @property
    def column_number(self):
        return tuple.__getitem__(self, 2)

    def __getitem__(self, item):
        raise TypeError

    def __repr__(self):
        return '@{file_name}:{line_number}:{column_number}'.format(
            file_name=self.file_name, line_number=self.line_number, column_number=self.column_number
        )


class LocationNOTSET(Location):
    def __new__(cls):
        return tuple.__new__(cls, ('', '', ''))

    @property
    def file_name(self):
        raise TypeError

    @property
    def line_number(self):
        raise TypeError

    @property
    def column_number(self):
        raise TypeError

    def __repr__(self):
        return 'Location Not Set.'

    def __nonzero__(self):
        return False


LocationNotSet = LocationNOTSET()
EOFLocation = Location('__EOF__', '', '')


class Str(str):
    # noinspection PyInitNewSignature
    def __new__(cls, value, location=LocationNotSet):
        value = str.__new__(cls, value)
        value._location = location
        return value

    @property
    def location(self):
        return self._location


def loc(obj):
    if isinstance(obj, Location):
        return obj
    return getattr(obj, 'location', LocationNotSet)