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