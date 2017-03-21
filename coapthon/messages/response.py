from coapthon import defines
from coapthon.messages.message import Message
from coapthon.messages.option import Option

__author__ = 'Giacomo Tanganelli'


class Response(Message):
    """
    Class to handle the Responses.
    """
    @property
    def location_path(self):
        """
        Return the Location-Path of the response.

        :rtype : String
        :return: the Location-Path option
        """
        value = []
        for option in self.options:
            if option.number == defines.OptionRegistry.LOCATION_PATH.number:
                value.append(str(option.value))
        return "/".join(value)

    @location_path.setter
    def location_path(self, path):
        """
        Set the Location-Path of the response.

        :type path: String
        :param path: the Location-Path as a string
        """
        path = path.strip("/")
        tmp = path.split("?")
        path = tmp[0]
        paths = path.split("/")
        for p in paths:
            option = Option()
            option.number = defines.OptionRegistry.LOCATION_PATH.number
            option.value = p
            self.add_option(option)
        # if len(tmp) > 1:
        #     query = tmp[1]
        #     self.location_query = query

    @location_path.deleter
    def location_path(self):
        """
        Delete the Location-Path of the response.
        """
        self.del_option_by_number(defines.OptionRegistry.LOCATION_PATH.number)

    @property
    def location_query(self):
        """
        Return the Location-Query of the response.

        :rtype : String
        :return: the Location-Query option
        """
        value = []
        for option in self.options:
            if option.number == defines.OptionRegistry.LOCATION_QUERY.number:
                value.append(option.value)
        return value

    @location_query.setter
    def location_query(self, value):
        """
        Set the Location-Query of the response.

        :type path: String
        :param path: the Location-Query as a string
        """
        del self.location_query
        queries = value.split("&")
        for q in queries:
            option = Option()
            option.number = defines.OptionRegistry.LOCATION_QUERY.number
            option.value = str(q)
            self.add_option(option)

    @location_query.deleter
    def location_query(self):
        """
        Delete the Location-Query of the response.
        """
        self.del_option_by_number(defines.OptionRegistry.LOCATION_QUERY.number)

    @property
    def max_age(self):
        """
        Return the MaxAge of the response.

        :rtype : int
        :return: the MaxAge option
        """
        value = defines.OptionRegistry.MAX_AGE.default
        for option in self.options:
            if option.number == defines.OptionRegistry.MAX_AGE.number:
                value = int(option.value)
        return value

    @max_age.setter
    def max_age(self, value):
        """
        Set the MaxAge of the response.

        :type value: int
        :param value: the MaxAge option
        """
        option = Option()
        option.number = defines.OptionRegistry.MAX_AGE.number
        option.value = int(value)
        self.del_option_by_number(defines.OptionRegistry.MAX_AGE.number)
        self.add_option(option)

    @max_age.deleter
    def max_age(self):
        """
        Delete the MaxAge of the response.
        """
        self.del_option_by_number(defines.OptionRegistry.MAX_AGE.number)
