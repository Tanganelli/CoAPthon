from coapthon2.messages.request import Request

__author__ = 'Giacomo Tanganelli'


class Matcher(object):
    def __init__(self, server):
        self._mid_received = {}
        self._token_received = {}
        self._mid_sent = {}
        self._token_sent = {}
        self._server = server

    def handle_request(self, message):
        assert isinstance(message, Request)
        if message.mid not in self._mid_received:
            self._token_received[message.token] = self._mid_received[message.mid] = message
            self._token_sent[message.token] = self._mid_sent[message.mid] = None
        else:
            message.duplicated = True
        return True

    def response_sent(self, mid):
        return self._mid_sent[mid]

    def send_previous_response(self, mid):
        response = self._mid_sent[mid]

    def send_ack(self, mid):
        pass

    def send_rst(self, mid):
        pass