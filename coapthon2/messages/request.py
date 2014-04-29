from coapthon2.messages.message import Message

__author__ = 'giacomo'


class Request(Message):
    def __init__(self):
        super(Request, self).__init__()
        self.code = None