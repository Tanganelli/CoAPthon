from coapthon2.layers.matcher import Matcher
from coapthon2.messages.request import Request

__author__ = 'Giacomo Tanganelli'


class Reliability(object):
    def __init__(self, server):
        self._server = server

    def handle_request(self, request):
        assert isinstance(request, Request)
        if request.duplicated:
            matcher = self._server.layer_stack.next
            assert isinstance(matcher, Matcher)
            response = matcher.response_sent(request.mid)
            #assert isinstance(request, Response)
            if response is not None:
                matcher.send_previous_response(request.mid)
            elif request.acknowledged:
                matcher.send_ack(request.mid)
            elif request.rejected:
                matcher.send_rst(request.mid)
            else:
                pass
            return False
        else:
            return True


