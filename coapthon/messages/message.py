from coapthon import defines
from coapthon.messages.option import Option

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
        # The type. One of {CON, NON, ACK or RST}.
        self._type = None
        # The 16-bit Message Identification.
        self._mid = None
        # The token, a 0-8 byte array.
        self.token = None
        # The set of options of this message.
        self._options = []
        # The payload of this message.
        self._payload = None
        # The destination address of this message.
        self.destination = None
        # The source address of this message.
        self.source = None
        # Indicates if the message has been acknowledged.
        self._acknowledged = False
        # Indicates if the message has been rejected.
        self._rejected = False
        # Indicates if the message has timeouted.
        self._timeouted = False
        # Indicates if the message has been canceled.
        self._canceled = False
        # Indicates if the message is a duplicate.
        self._duplicate = False
        # The timestamp
        self._timestamp = None
        # The code
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
            ret = self.already_in(option)
            if ret:
                raise TypeError("Option : %s is not repeatable", name)
            else:
                self._options.append(option)
        else:
            self._options.append(option)

    def del_option(self, option):
        """
        Delete an option from the message

        :type option: coapthon2.messages.option.Option
        :param option: the option
        """
        try:
            while True:
                self._options.remove(option)
        except ValueError:
            pass

    def del_option_name(self, name):
        """
        Delete an option from the message by name

        :param name: option name
        """
        for o in self._options:
            assert isinstance(o, Option)
            if o.number == defines.inv_options[name]:
                self._options.remove(o)

    @property
    def mid(self):
        """
        Return the mid of the message.

        :return: the MID
        """
        return self._mid

    @mid.setter
    def mid(self, m):
        """
        Sets the MID of the message.

        :param m: the MID
        :raise AttributeError: if m is not int or cannot be represented on 16 bits.
        """
        if not isinstance(m, int) or m > 65536:
            raise AttributeError
        self._mid = m

    @property
    def type(self):
        """
        Return the type of the message.

        :return: the type
        """
        return self._type

    @type.setter
    def type(self, t):
        """
        Sets the type of the message.

        :param t: the type
        :raise AttributeError: if t is not a valid type
        """
        if not isinstance(t, int) or t not in defines.types:
            raise AttributeError
        self._type = t

    @property
    def payload(self):
        return self._payload

    @payload.setter
    def payload(self, value):
        if isinstance(value, tuple):
            content_type, payload = value
            option = Option()
            option.number = defines.inv_options["Content-Type"]
            option.value = content_type
            self.add_option(option)
            self._payload = payload
        else:
            self._payload = value

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
        ack._mid = message.mid
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
        rst._mid = message.mid
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
        msg += "MID: " + str(self._mid) + "\n"
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
        msg += str(self._payload) + "\n"
        return msg

    @property
    def etag(self):
        """
        Get the ETag option of the message.

        :return: the ETag values or [] if not specified by the request
        """
        value = []
        for option in self.options:
            if option.number == defines.inv_options['ETag']:
                value.append(option.value)
        return value

    @etag.setter
    def etag(self, etag):
        """
        Add an ETag option to the message.

        :param etag: the etag
        """
        option = Option()
        option.number = defines.inv_options['ETag']
        option.value = etag
        self.add_option(option)

    @etag.deleter
    def etag(self):
        """
        Delete an ETag from a message.

        """
        self.del_option_name("ETag")

    @property
    def content_type(self):
        """
        Get the Content-Type option of a response.

        :return: the Content-Type value or 0 if not specified by the response
        """
        value = 0
        for option in self.options:
            if option.number == defines.inv_options['Content-Type']:
                value = int(option.value)
        return value

    @content_type.setter
    def content_type(self, content_type):
        """
        Set the Content-Type option of a response.

        :type content_type: int
        :param content_type: the Content-Type
        """
        option = Option()
        option.number = defines.inv_options['Content-Type']
        option.value = int(content_type)
        self.add_option(option)

    def already_in(self, option):
        for opt in self._options:
            if option.number == opt.number:
                return True
        return False