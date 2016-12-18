from coapthon import defines
from coapthon.utils import byte_len

__author__ = 'Giacomo Tanganelli'


class Option(object):
    def __init__(self):
        self._number = None
        self._value = None

    @property
    def number(self):
        """

        """
        return self._number

    @number.setter
    def number(self, value):
        """

        :type value: Integer
        :param value:
        """
        self._number = value

    @property
    def value(self):
        """

        """
        if type(self._value) is None:
            self._value = bytearray()
        opt_type = defines.OptionRegistry.LIST[self._number].value_type
        if opt_type == defines.INTEGER:
            if byte_len(self._value) > 0:
                return int(self._value)
            else:
                return defines.OptionRegistry.LIST[self._number].default
        return self._value

    @value.setter
    def value(self, value):
        """

        :type value: String
        :param value:
        """
        if type(value) is str:
            value = bytearray(value, "utf-8")
        elif type(value) is int and byte_len(value) != 0:
            value = value
        elif type(value) is int and byte_len(value) == 0:
            value = 0
        self._value = value

    @property
    def length(self):
        """

        :rtype : Integer
        """
        if isinstance(self._value, int):
            return byte_len(self._value)
        if self._value is None:
            return 0
        return len(self._value)

    def is_safe(self):
        """

        :rtype : Boolean
        """
        if self._number == defines.OptionRegistry.URI_HOST.number \
                or self._number == defines.OptionRegistry.URI_PORT.number \
                or self._number == defines.OptionRegistry.URI_PATH.number \
                or self._number == defines.OptionRegistry.MAX_AGE.number \
                or self._number == defines.OptionRegistry.URI_QUERY.number \
                or self._number == defines.OptionRegistry.PROXY_URI.number \
                or self._number == defines.OptionRegistry.PROXY_SCHEME.number:
            return False
        return True

    @property
    def name(self):
        """

        :rtype : String
        """
        return defines.OptionRegistry.LIST[self._number].name

    def __str__(self):
        """

        :rtype : String
        """
        return self.name + ": " + str(self.value) + "\n"

    def __eq__(self, other):
        """

        :type other: Option
        :param other:
        :rtype : Boolean
        """
        return self.__dict__ == other.__dict__
