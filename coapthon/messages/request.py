from coapthon import defines
from coapthon.messages.message import Message
from coapthon.messages.option import Option

__author__ = 'Giacomo Tanganelli'


class Request(Message):
    """
    Class to handle the Requests.
    """
    def __init__(self):
        """
        Initialize a Request message.

        """
        super(Request, self).__init__()

    @property
    def uri_path(self):
        """
        Return the Uri-Path of a request

        :rtype : String
        :return: the Uri-Path
        """
        value = []
        for option in self.options:
            if option.number == defines.OptionRegistry.URI_PATH.number:
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
            option.number = defines.OptionRegistry.URI_PATH.number
            option.value = p
            self.add_option(option)
        if len(tmp) > 1:
            query = tmp[1]
            self.uri_query = query

    @uri_path.deleter
    def uri_path(self):
        """
        Delete the Uri-Path of a request.
        """
        self.del_option_by_number(defines.OptionRegistry.URI_PATH.number)

    @property
    def uri_query(self):
        """
        Get the Uri-Query of a request.

        :return: the Uri-Query
        :rtype : String
        :return: the Uri-Query string
        """
        value = []
        for option in self.options:
            if option.number == defines.OptionRegistry.URI_QUERY.number:
                value.append(str(option.value))
        return "&".join(value)

    @uri_query.setter
    def uri_query(self, value):
        """
        Adds a query.

        :param value: the query
        """
        del self.uri_query
        queries = value.split("&")
        for q in queries:
            option = Option()
            option.number = defines.OptionRegistry.URI_QUERY.number
            option.value = str(q)
            self.add_option(option)

    @uri_query.deleter
    def uri_query(self):
        """
        Delete a query.
        """
        self.del_option_by_number(defines.OptionRegistry.URI_QUERY.number)

    @property
    def accept(self):
        """
        Get the Accept option of a request.

        :return: the Accept value or None if not specified by the request
        :rtype : String
        """
        for option in self.options:
            if option.number == defines.OptionRegistry.ACCEPT.number:
                return option.value
        return None

    @accept.setter
    def accept(self, value):
        """
        Add an Accept option to a request.

        :param value: the Accept value
        """
        if value in defines.Content_types.values():
            option = Option()
            option.number = defines.OptionRegistry.ACCEPT.number
            option.value = value
            self.add_option(option)

    @accept.deleter
    def accept(self):
        """
        Delete the Accept options of a request.
        """
        self.del_option_by_number(defines.OptionRegistry.ACCEPT.number)

    @property
    def if_match(self):
        """
        Get the If-Match option of a request.

        :return: the If-Match values or [] if not specified by the request
        :rtype : list
        """
        value = []
        for option in self.options:
            if option.number == defines.OptionRegistry.IF_MATCH.number:
                value.append(option.value)
        return value

    @if_match.setter
    def if_match(self, values):
        """
        Set the If-Match option of a request.

        :param values: the If-Match values
        :type values : list
        """
        assert isinstance(values, list)
        for v in values:
            option = Option()
            option.number = defines.OptionRegistry.IF_MATCH.number
            option.value = v
            self.add_option(option)

    @if_match.deleter
    def if_match(self):
        """
        Delete the If-Match options of a request.
        """
        self.del_option_by_number(defines.OptionRegistry.IF_MATCH.number)

    @property
    def if_none_match(self):
        """
        Get the if-none-match option of a request.

        :return: True, if if-none-match is present
        :rtype : bool
        """
        for option in self.options:
            if option.number == defines.OptionRegistry.IF_NONE_MATCH.number:
                return True
        return False

    def add_if_none_match(self):
        """
        Add the if-none-match option to the request.
        """
        option = Option()
        option.number = defines.OptionRegistry.IF_NONE_MATCH.number
        option.value = None
        self.add_option(option)

    @if_none_match.deleter
    def if_none_match(self):
        """
        Delete the if-none-match option in the request.
        """
        self.del_option_by_number(defines.OptionRegistry.IF_NONE_MATCH.number)

    @property
    def proxy_uri(self):
        """
        Get the Proxy-Uri option of a request.

        :return: the Proxy-Uri values or None if not specified by the request
        :rtype : String
        """
        for option in self.options:
            if option.number == defines.OptionRegistry.PROXY_URI.number:
                return option.value
        return None

    @proxy_uri.setter
    def proxy_uri(self, value):
        """
        Set the Proxy-Uri option of a request.

        :param value: the Proxy-Uri value
        """
        option = Option()
        option.number = defines.OptionRegistry.PROXY_URI.number
        option.value = str(value)
        self.add_option(option)

    @proxy_uri.deleter
    def proxy_uri(self):
        """
        Delete the Proxy-Uri option of a request.
        """
        self.del_option_by_number(defines.OptionRegistry.PROXY_URI.number)

    @property
    def proxy_schema(self):
        """
        Get the Proxy-Schema option of a request.

        :return: the Proxy-Schema values or None if not specified by the request
        :rtype : String
        """
        for option in self.options:
            if option.number == defines.OptionRegistry.PROXY_SCHEME.number:
                return option.value
        return None

    @proxy_schema.setter
    def proxy_schema(self, value):
        """
        Set the Proxy-Schema option of a request.

        :param value: the Proxy-Schema value
        """
        option = Option()
        option.number = defines.OptionRegistry.PROXY_SCHEME.number
        option.value = str(value)
        self.add_option(option)

    @proxy_schema.deleter
    def proxy_schema(self):
        """
        Delete the Proxy-Schema option of a request.
        """
        self.del_option_by_number(defines.OptionRegistry.PROXY_SCHEME.number)

