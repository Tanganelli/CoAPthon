__author__ = 'giacomo'


class Option(object):
    def __init__(self):
        self._number = None
        self._value = None

    @property
    def number(self):
        return self._number

    @number.setter
    def number(self, number):
        self._number = number

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._value = value