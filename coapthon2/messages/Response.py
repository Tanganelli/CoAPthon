from coapthon2.messages.message import Message

__author__ = 'Giacomo Tanganelli'


class Response(Message):
    def __init__(self):
        super(Response, self).__init__()
        self.code = None
