from coapthon2 import defines
from coapthon2.messages.message import Message

__author__ = 'Giacomo Tanganelli'
__version__ = "2.0"


class Request(Message):
    def __init__(self):
        super(Request, self).__init__()
        self.code = None

    @property
    def uri_path(self):
        value = ""
        for option in self.options:
            if option.number == defines.inv_options['Uri-Path']:
                value += option.value + '/'
        value = value[:-1]
        return value

    @property
    def observe(self):
        for option in self.options:
            if option.number == defines.inv_options['Observe']:
                return True
        return False

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