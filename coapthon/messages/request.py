from coapthon import defines
from coapthon.messages.message import Message
from coapthon.messages.option import Option

__author__ = 'Giacomo Tanganelli'
__version__ = "2.0"


class Request(Message):
    """
    Represent a Request message.
    """
    def __init__(self):
        """
        Initialize a Request message.

        """
        super(Request, self).__init__()

    @property
    def uri_path(self):
        """
        Get the Uri-Path of a request.

        :return: the Uri-Path
        """
        value = []
        for option in self.options:
            if option.number == defines.inv_options['Uri-Path']:
                value.append(str(option.value) + '/')
        value = "".join(value)
        value = value[:-1]
        return value

    @uri_path.setter
    def uri_path(self, path):
        """
        Set the Uri-Path of a request.

        :param path: the Uri-Path
        """
        path = path.strip("/")
        tmp = path.split("?")
        path = tmp[0]
        paths = path.split("/")
        for p in paths:
            option = Option()
            option.number = defines.inv_options['Uri-Path']
            option.value = p
            self.add_option(option)
        if len(tmp) > 1:
            query = tmp[1]
            queries = query.split("&")
            for q in queries:
                option = Option()
                option.number = defines.inv_options['Uri-Query']
                option.value = q
                self.add_option(option)

    @property
    def observe(self):
        """
        Check if the request is an observing request.

        :return: 0, if the request is an observing request
        """
        for option in self.options:
            if option.number == defines.inv_options['Observe']:
                if option.value is None:
                    return 0
                return option.value
        return 1

    @observe.setter
    def observe(self, ob):
        """
        Add the Observe option.

        :param ob: observe count
        """
        option = Option()
        option.number = defines.inv_options['Observe']
        option.value = ob
        self.del_option_name("Observe")
        self.add_option(option)

    @property
    def blockwise(self):
        """
        Check if the request is a blockwise request.

        :return: 1, if the request is an blockwise request
        """
        for option in self.options:
            if option.number == defines.inv_options['Block1'] or option.number == defines.inv_options['Block2']:
                return 1
        return 0

    @property
    def query(self):
        """
        Get the Uri-Query of a request.

        :return: the Uri-Query
        """
        value = []
        for option in self.options:
            if option.number == defines.inv_options['Uri-Query']:
                value.append(option.value)
        return value

    @query.setter
    def query(self, q):
        option = Option()
        option.number = defines.inv_options['Uri-Query']
        option.value = str(q)
        self.add_option(option)

    @property
    def accept(self):
        """
        Get the Accept option of a request.

        :return: the Accept value or None if not specified by the request
        """
        for option in self.options:
            if option.number == defines.inv_options['Accept']:
                return option.value
        return None

    @property
    def if_match(self):
        """
        Get the If-Match option of a request.

        :return: the If-Match values or [] if not specified by the request
        """
        value = []
        for option in self.options:
            if option.number == defines.inv_options['If-Match']:
                value.append(option.value)
        return value

    @property
    def has_if_match(self):
        """
        Check if the request has the If-Match option.

        :return: True, if the request has the If-Match option.
        """
        for option in self.options:
            if option.number == defines.inv_options['If-Match']:
                return True
        return False

    @property
    def has_if_none_match(self):
        """
        Check if the request has the If-None-Match option.

        :return: True, if the request has the If-None-Match option.
        """
        for option in self.options:
            if option.number == defines.inv_options['If-None-Match']:
                return True
        return False

    @property
    def proxy_uri(self):
        """
        Get the Proxy-Uri option of a request.

        :return: the Proxy-Uri values or None if not specified by the request
        """
        value = None
        for option in self.options:
            if option.number == defines.inv_options['Proxy-Uri']:
                value = option.value
        return value

    @proxy_uri.setter
    def proxy_uri(self, uri):
        """
        Set the Proxy-Uri option of a request.

        :param uri: the Proxy-Uri values
        """
        option = Option()
        option.number = defines.inv_options['Proxy-Uri']
        option.value = str(uri)
        self.add_option(option)