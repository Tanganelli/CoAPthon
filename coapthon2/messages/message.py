from coapthon2 import defines
from coapthon2.messages.option import Option

__author__ = 'Giacomo Tanganelli'


class Message(object):
    def __init__(self):
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

    @property
    def options(self):
        return self._options

    def add_option(self, option):
        assert isinstance(option, Option)
        name, type_value, repeatable = defines.options[option.number]
        if not repeatable:
            try:
                self._options.index(option)
                raise TypeError("Option : %s is not repeatable", name)
            except ValueError:
                self._options.append(option)
        else:
            self._options.append(option)

    def del_option(self, option):
        assert isinstance(option, Option)
        try:
            while True:
                self._options.remove(option)
        except ValueError:
            pass

    @property
    def duplicated(self):
        """
        Checks if this message is a duplicate.

        @return: True, if is a duplicate
        """
        return self._duplicate

    @duplicated.setter
    def duplicated(self, d):
        """
        Marks this message as a duplicate.

        @param d: if a duplicate
        """
        assert isinstance(d, bool)
        self._duplicate = d

    @property
    def acknowledged(self):
        """
        Checks if is this message has been acknowledged.

        @return: True, if is acknowledged
        """
        return self._acknowledged

    @acknowledged.setter
    def acknowledged(self, a):
        """
        Marks this message as acknowledged.

        @param a: if acknowledged
        """
        assert isinstance(a, bool)
        self._acknowledged = a

    @property
    def rejected(self):
        """
        Checks if this message has been rejected.

        @return: True, if is rejected
        """
        return self._rejected

    @rejected.setter
    def rejected(self, r):
        """
        Marks this message as rejected.

        @param r: if rejected
        """
        assert isinstance(r, bool)
        self._rejected = r

    @property
    def timeouted(self):
        """
        Checks if this message has timeouted. Confirmable messages in particular
        might timeout.

        @return: True, if has timeouted
        """
        return self._timeouted

    @timeouted.setter
    def timeouted(self, t):
        """
        Marks this message as timeouted. Confirmable messages in particular might
        timeout.

        @param t: if timeouted
        """
        assert isinstance(t, bool)
        self._timeouted = t

    @property
    def cancelled(self):
        """
        Checks if this message has been canceled.

        @return: True, if is canceled
        """
        return self._canceled

    @cancelled.setter
    def cancelled(self, c):
        """
        Marks this message as canceled.

        @param c: if canceled
        """
        assert isinstance(c, bool)
        self._canceled = c