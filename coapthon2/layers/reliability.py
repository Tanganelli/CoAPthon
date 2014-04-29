from coapthon2.messages.request import Request

__author__ = 'jacko'


class Reliability(object):
    def handle_request(self, message):
        assert isinstance(message, Request)
