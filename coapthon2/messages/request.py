from coapthon2 import defines
from coapthon2.messages.message import Message
from coapthon2.messages.option import Option

__author__ = 'Giacomo Tanganelli'
__version__ = "2.0"


class Request(Message):
    def __init__(self):
        super(Request, self).__init__()

    @property
    def uri_path(self):
        value = ""
        for option in self.options:
            if option.number == defines.inv_options['Uri-Path']:
                value += option.value + '/'
        value = value[:-1]
        return value

    @uri_path.setter
    def uri_path(self, path):
        path = path.strip("/")
        paths = path.split("/")
        for p in paths:
            option = Option()
            option.number = defines.inv_options['Uri-Path']
            option.value = p
            self.add_option(option)

    @property
    def observe(self):
        for option in self.options:
            if option.number == defines.inv_options['Observe']:
                if option.value is None:
                    return 0
                return option.value
        return 1

    @property
    def query(self):
        value = []
        for option in self.options:
            if option.number == defines.inv_options['Uri-Query']:
                value.append(option.value)
        return value

    @property
    def content_type(self):
        for option in self.options:
            if option.number == defines.inv_options['Content-Type']:
                return option.value
        return None

    @property
    def accept(self):
        for option in self.options:
            if option.number == defines.inv_options['Accept']:
                return option.value
        return None

    @property
    def etag(self):
        value = []
        for option in self.options:
            if option.number == defines.inv_options['ETag']:
                value.append(option.value)
        return value

    @property
    def if_match(self):
        value = []
        for option in self.options:
            if option.number == defines.inv_options['If-Match']:
                value.append(option.value)
        return value

    @property
    def has_if_match(self):
        for option in self.options:
            if option.number == defines.inv_options['If-Match']:
                return True
        return False

    @property
    def has_if_none_match(self):
        for option in self.options:
            if option.number == defines.inv_options['If-None-Match']:
                return True
        return False