from bitstring import BitArray
from coapthon2 import defines
from coapthon2.utils import bit_len

__author__ = 'Giacomo Tanganelli'
__version__ = "2.0"


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
        if type(self._value) is None:
            self._value = BitArray()
        name, opt_type, repeatable, defaults = defines.options[self._number]
        if opt_type == defines.INTEGER:
            if self._value.len > 0:
                return self._value.uint
            else:
                return defaults
        return self._value.tobytes()

    @value.setter
    def value(self, val):
        if type(val) is str:
            val = BitArray(bytes=val, length=len(val) * 8)
        if type(val) is int and bit_len(val) != 0:
            val = BitArray(uint=val, length=bit_len(val) * 8)
        if type(val) is int and bit_len(val) == 0:
            val = BitArray()
        assert(type(val) is BitArray)
        self._value = val

    @property
    def raw_value(self):
        """
        Gets the option value.

        @return: the option value
        """
        if type(self._value) is None:
            self._value = BitArray()
        return self._value

    @property
    def length(self):
        assert(type(self._value) is BitArray)
        return len(self._value.tobytes())

    def __str__(self):
        name, opt_type, repeatable, defaults = defines.options[self._number]
        if name == "ETag":
            return name + ": " + str(self.raw_value) + "\n"
        else:
            return name + ": " + str(self.value) + "\n"