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
        self.options = None
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