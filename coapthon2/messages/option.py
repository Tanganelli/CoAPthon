from bitstring import BitArray
from coapthon2 import defines
from coapthon2.utils import bit_len

__author__ = 'Giacomo Tanganelli'
__version__ = "2.0"


class Option(object):
    """
    Represent a CoAP option.
    """
    def __init__(self):
        """
        Initialize an option.

        """
        self._number = None
        self._value = None

    @property
    def number(self):
        """
        Get the option number.

        :return: the option number
        """
        return self._number

    @number.setter
    def number(self, number):
        """
        Set the option number.

        :param number: the number
        """
        self._number = number

    @property
    def value(self):
        """
        Get the option value.


        :return: the option value as bytes
        """
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
        """
        Sets the option value.

        :param val: the value
        """
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
        Get the option value.

        :return: the option value as BitArray
        """
        if type(self._value) is None:
            self._value = BitArray()
        return self._value

    @property
    def length(self):
        """
        Get the len of the option value

        :return: the len of the option value
        """
        assert(type(self._value) is BitArray)
        return len(self._value.tobytes())

    @property
    def safe(self):
        if self._number == defines.inv_options["Uri-Host"] or self._number == defines.inv_options["Uri-Port"] \
                or self._number == defines.inv_options["Uri-Path"] or self._number == defines.inv_options["Max-Age"] \
                or self._number == defines.inv_options["Uri-Query"] \
                or self._number == defines.inv_options["Proxy-Uri"] \
                or self._number == defines.inv_options["Proxy-Scheme"]:
            return False
        return True

    @property
    def name(self):
        return defines.options[self._number][0]

    def __str__(self):
        """
        Return the option as a formatted string.

        :return: the string representing the option
        """
        name, opt_type, repeatable, defaults = defines.options[self._number]
        if name == "ETag":
            return name + ": " + str(self.raw_value) + "\n"
        else:
            return name + ": " + str(self.value) + "\n"

    def __eq__(self, other):
        return self.__dict__ == other.__dict__