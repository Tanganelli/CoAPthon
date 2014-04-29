from coapthon2 import defines
from coapthon2.messages.option import Option

__author__ = 'giacomo'


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
        assert (type(option) is Option)
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
        assert (type(option) is Option)
        try:
            while True:
                self._options.remove(option)
        except ValueError:
            pass
