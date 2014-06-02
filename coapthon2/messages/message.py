from coapthon2 import defines
from coapthon2.messages.option import Option

__author__ = 'Giacomo Tanganelli'
__version__ = "2.0"


class Message(object):
    """
    Manage messages.
    """
    def __init__(self):

        """
        Initialize a CoAP Message.

        """
        ## The type. One of {CON, NON, ACK or RST}.
        self.type = None
        ## The 16-bit Message Identification.
        self.mid = None
        ## The token, a 0-8 byte array.
        self.token = None
        ## The set of options of this message.
        self._options = []
        ## The payload of this message.
        self.payload = None
        ## The destination address of this message.
        self.destination = None
        ## The source address of this message.
        self.source = None
        ## Indicates if the message has been acknowledged.
        self._acknowledged = False
        ## Indicates if the message has been rejected.
        self._rejected = False
        ## Indicates if the message has timeouted.
        self._timeouted = False
        ## Indicates if the message has been canceled.
        self._canceled = False
        ## Indicates if the message is a duplicate.
        self._duplicate = False
        ## The timestamp
        self._timestamp = None
        ## The code
        self.code = None

    @property
    def options(self):
        """
        Property for retrieving the options of the message.

        :return: the options
        """
        return self._options

    def add_option(self, option):
        """
        Add an option to the message.

        :type option: coapthon2.messages.option.Option
        :param option: the option
        :raise TypeError: if the option is not repeatable and such option is already present in the message
        """
        assert isinstance(option, Option)
        name, type_value, repeatable, defaults = defines.options[option.number]
        if not repeatable:
            try:
                self._options.index(option)
                raise TypeError("Option : %s is not repeatable", name)
            except ValueError:
                self._options.append(option)
        else:
            self._options.append(option)

    def del_option(self, option):
        """
        Delete an option from the message

        :type option: coapthon2.messages.option.Option
        :param option: the option
        """
        assert isinstance(option, Option)
        try:
            while True:
                self._options.remove(option)
        except ValueError:
            pass

    def del_option_name(self, name):
        for o in self._options:
            assert isinstance(o, Option)
            if o.number == defines.inv_options[name]:
                self._options.remove(o)

    @property
    def duplicated(self):
        """
        Checks if this message is a duplicate.

        :return: True, if is a duplicate
        """
        return self._duplicate

    @duplicated.setter
    def duplicated(self, d):
        """
        Marks this message as a duplicate.

        :param d: if a duplicate
        """
        assert isinstance(d, bool)
        self._duplicate = d

    @property
    def acknowledged(self):
        """
        Checks if is this message has been acknowledged.

        :return: True, if is acknowledged
        """
        return self._acknowledged

    @acknowledged.setter
    def acknowledged(self, a):
        """
        Marks this message as acknowledged.

        :param a: if acknowledged
        """
        assert isinstance(a, bool)
        self._acknowledged = a

    @property
    def rejected(self):
        """
        Checks if this message has been rejected.

        :return: True, if is rejected
        """
        return self._rejected

    @rejected.setter
    def rejected(self, r):
        """
        Marks this message as rejected.

        :param r: if rejected
        """
        assert isinstance(r, bool)
        self._rejected = r

    @property
    def timeouted(self):
        """
        Checks if this message has timeouted. Confirmable messages in particular
        might timeout.

        :return: True, if has timeouted
        """
        return self._timeouted

    @timeouted.setter
    def timeouted(self, t):
        """
        Marks this message as timeouted. Confirmable messages in particular might
        timeout.

        :param t: if timeouted
        """
        assert isinstance(t, bool)
        self._timeouted = t

    @property
    def cancelled(self):
        """
        Checks if this message has been canceled.

        :return: True, if is canceled
        """
        return self._canceled

    @cancelled.setter
    def cancelled(self, c):
        """
        Marks this message as canceled.

        :param c: if canceled
        """
        assert isinstance(c, bool)
        self._canceled = c

    @staticmethod
    def new_ack(message):
        """
        Create a new acknowledgment for the specified message.

        :param message: the message to acknowledge
        :return: the acknowledgment
        """
        ack = Message()
        types = {v: k for k, v in defines.types.iteritems()}
        ack.type = types['ACK']
        ack.mid = message.mid
        ack.code = 0
        ack.token = None
        ack.destination = message.source
        return ack

    @staticmethod
    def new_rst(message):
        """
        Create a new reset message for the specified message.

        :param message: the message to reject
        :return: the rst message
        """
        rst = Message()
        types = {v: k for k, v in defines.types.iteritems()}
        rst.type = types['RST']
        rst.mid = message.mid
        rst.token = None
        rst.code = 0
        rst.destination = message.source
        return rst

    def __str__(self):
        """
        Return the message as a formatted string.

        :return: the string representing the message
        """
        msg = "Source: " + str(self.source) + "\n"
        msg += "Destination: " + str(self.destination) + "\n"
        msg += "Type: " + str(defines.types[self.type]) + "\n"
        msg += "MID: " + str(self.mid) + "\n"
        if self.code is None:
            self.code = 0
        try:
            msg += "Code: " + str(defines.inv_responses[self.code]) + "\n"
        except KeyError:
            msg += "Code: " + str(defines.codes[self.code]) + "\n"
        msg += "Token: " + str(self.token) + "\n"
        for opt in self._options:
            msg += str(opt)
        msg += "Payload: " + "\n"
        msg += str(self.payload) + "\n"
        return msg