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
        return '{cls_name}(@{file_name}:{line_number}:{column_number})'.format(
            file_name=self.file_name,
            line_number=self.line_number,
            column_number=self.column_number,
            cls_name=self.__class__.__name__
        )


class EOLLocation(Location):  # End of Line Location
    pass


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


class LocatedStr(str):
    # noinspection PyInitNewSignature
    def __new__(cls, value, location=LocationNotSet):
        value = str.__new__(cls, value)
        value._location = location
        return value

    @property
    def location(self):
        return self._location


class Str(LocatedStr):
    pass


class NewLineStr(LocatedStr):
    pass


def loc(obj, default=LocationNotSet):
    if isinstance(obj, Location):
        return obj
    return getattr(obj, 'location', default)


def line_number(obj):
    return loc(obj).line_number


def column_number(obj):
    return loc(obj).column_number
