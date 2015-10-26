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
    def last_block(self):
        if not self.blockwise:
            return True
        else:
            num, m, size = self.block1
            if m == 0:
                return True
        return False

    def add_block2(self, num, m, size):
        """
        Add and format a Block2 option to a request.

        :param num: num
        :param m: more blocks
        :param size: size in byte
        """
        option = Option()
        option.number = defines.inv_options['Block2']
        if size > 1024:
            szx = 6
        elif 512 < size <= 1024:
            szx = 6
        elif 256 < size <= 512:
            szx = 5
        elif 128 < size <= 256:
            szx = 4
        elif 64 < size <= 128:
            szx = 3
        elif 32 < size <= 64:
            szx = 2
        elif 16 < size <= 32:
            szx = 1
        else:
            szx = 0
        value = (num << 4)
        value |= (m << 3)
        value |= szx

        option.value = value
        self.add_option(option)

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

    def add_query(self, q):
        """
        Adds a query.
        :param q: the query
        """
        queries = q.split("&")
        for q in queries:
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