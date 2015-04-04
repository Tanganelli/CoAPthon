from bitstring import Bits, BitArray
from coapthon2 import defines
from coapthon2.messages.message import Message
from coapthon2.messages.option import Option

__author__ = 'Giacomo Tanganelli'


class Response(Message):
    """
    Represent a Response message.
    """
    def __init__(self):
        """
        Initialize a Response message.

        """
        super(Response, self).__init__()

    @property
    def location_path(self):
        """
        Get the Location-Path option of a response.

        :return: the Location-Path
        """
        value = []
        for option in self.options:
            if option.number == defines.inv_options['Location-Path']:
                value.append(option.value)
        return value

    @location_path.setter
    def location_path(self, lp):
        """
        Set the Location-Path option of a response.

        :param lp: the Location-Path
        """
        if not isinstance(lp, list):
            lp = [lp]
        for o in lp:
            option = Option()
            option.number = defines.inv_options['Location-Path']
            option.value = o
            self.add_option(option)

    @property
    def location_query(self):
        """
        Get the Location-Query option of a response.

        :return: the Location-Query
        """
        value = []
        for option in self.options:
            if option.number == defines.inv_options['Location-Query']:
                value.append(option.value)
        return value

    @location_query.setter
    def location_query(self, lq):
        """
        Set the Location-Query option of a response.

        :param lq: the Location-Query
        """
        if not isinstance(lq, list):
            lq = [lq]
        for o in lq:
            option = Option()
            option.number = defines.inv_options['Location-Query']
            option.value = o
            self.add_option(option)

    @property
    def max_age(self):
        """
        Get the Max-Age option of a response.

        :return: the Max-Age value or 0 if not specified by the response
        """
        value = 0
        for option in self.options:
            if option.number == defines.inv_options['Max-Age']:
                value = int(option.value)
        return value

    @max_age.setter
    def max_age(self, max_age):
        """
        Set the Max-Age option of a response.

        :param max_age: the Max-Age in seconds
        """
        option = Option()
        option.number = defines.inv_options['Max-Age']
        option.value = int(max_age)
        self.add_option(option)

    @property
    def observe(self):
        """
        Get the Observe option of a response.

        :return: the Observe value
        """
        value = 0
        for option in self.options:
            if option.number == defines.inv_options['Observe']:
                value = int(option.value)
        return value

    @property
    def block2(self):
        value = 0
        for option in self.options:
            if option.number == defines.inv_options['Block2']:
                value = option.raw_value
        return value

    @block2.setter
    def block2(self, value):
        option = Option()
        option.number = defines.inv_options['Block2']
        num, m, size = value
        m = Bits(uint=m, length=1)
        size = Bits(uint=size, length=3)
        if num <= 15:
            num = Bits(uint=num, length=4)
        elif num <= pow(2, 12) - 1:
            num = Bits(uint=num, length=12)
        else:
            num = Bits(uint=num, length=20)
        value = BitArray()
        value.append(num)
        value.append(m)
        value.append(size)
        option.value = value.tobytes()
        self.add_option(option)

    @property
    def block1(self):
        value = 0
        for option in self.options:
            if option.number == defines.inv_options['Block1']:
                value = option.raw_value
        return value

    @block1.setter
    def block1(self, value):
        option = Option()
        option.number = defines.inv_options['Block1']
        num, m, size = value
        m = Bits(uint=m, length=1)
        size = Bits(uint=size, length=3)
        if num <= 15:
            num = Bits(uint=num, length=4)
        elif num <= pow(2, 12) - 1:
            num = Bits(uint=num, length=12)
        else:
            num = Bits(uint=num, length=20)
        value = BitArray()
        value.append(num)
        value.append(m)
        value.append(size)
        option.value = value.tobytes()
        self.add_option(option)