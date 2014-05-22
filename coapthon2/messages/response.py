from coapthon2 import defines
from coapthon2.messages.message import Message
from coapthon2.messages.option import Option

__author__ = 'Giacomo Tanganelli'


class Response(Message):
    def __init__(self):
        super(Response, self).__init__()
        self.code = None

    @property
    def content_type(self):
        value = 0
        for option in self.options:
            if option.number == defines.inv_options['Content-Type']:
                value = int(option.value)
        return value

    @content_type.setter
    def content_type(self, content_type):
        option = Option()
        option.number = defines.inv_options['Content-Type']
        option.value = int(content_type)
        self.options.append(option)

    @property
    def etag(self):
        value = []
        for option in self.options:
            if option.number == defines.inv_options['ETag']:
                value.append(option.value)
        return value

    @etag.setter
    def etag(self, etag):
        option = Option()
        option.number = defines.inv_options['ETag']
        option.value = etag
        self.options.append(option)

    @property
    def location_path(self):
        value = []
        for option in self.options:
            if option.number == defines.inv_options['Location-Path']:
                value.append(option.value)
        return value

    @location_path.setter
    def location_path(self, lp):
        if not isinstance(lp, list):
            lp = [lp]
        for o in lp:
            option = Option()
            option.number = defines.inv_options['Location-Path']
            option.value = o
            self.options.append(option)

    @property
    def location_query(self):
        value = []
        for option in self.options:
            if option.number == defines.inv_options['Location-Query']:
                value.append(option.value)
        return value

    @location_query.setter
    def location_query(self, lp):
        if not isinstance(lp, list):
            lp = [lp]
        for o in lp:
            option = Option()
            option.number = defines.inv_options['Location-Query']
            option.value = o
            self.options.append(option)