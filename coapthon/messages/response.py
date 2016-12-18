from coapthon import defines
from coapthon.messages.message import Message
from coapthon.messages.option import Option

__author__ = 'Giacomo Tanganelli'


class Response(Message):
    @property
    def location_path(self):
        """

        :rtype : String
        """
        value = []
        for option in self.options:
            if option.number == defines.OptionRegistry.LOCATION_PATH.number:
                value.append(str(option.value))
        return "/".join(value)

    @location_path.setter
    def location_path(self, path):
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
        self.del_option_by_number(defines.OptionRegistry.LOCATION_PATH.number)

    @property
    def location_query(self):
        """

        :rtype : String
        """
        value = []
        for option in self.options:
            if option.number == defines.OptionRegistry.LOCATION_QUERY.number:
                value.append(option.value)
        return value

    @location_query.setter
    def location_query(self, value):
        del self.location_query
        queries = value.split("&")
        for q in queries:
            option = Option()
            option.number = defines.OptionRegistry.LOCATION_QUERY.number
            option.value = str(q)
            self.add_option(option)

    @location_query.deleter
    def location_query(self):
        self.del_option_by_number(defines.OptionRegistry.LOCATION_QUERY.number)

    @property
    def max_age(self):
        """

        :rtype : Integer
        """
        value = defines.OptionRegistry.MAX_AGE.default
        for option in self.options:
            if option.number == defines.OptionRegistry.MAX_AGE.number:
                value = int(option.value)
        return value

    @max_age.setter
    def max_age(self, value):
        option = Option()
        option.number = defines.OptionRegistry.MAX_AGE.number
        option.value = int(value)
        self.del_option_by_number(defines.OptionRegistry.MAX_AGE.number)
        self.add_option(option)

    @max_age.deleter
    def max_age(self):
        self.del_option_by_number(defines.OptionRegistry.MAX_AGE.number)
