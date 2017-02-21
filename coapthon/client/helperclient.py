import random
from multiprocessing import Queue
import threading
from coapthon.messages.message import Message
from coapthon import defines
from coapthon.client.coap import CoAP
from coapthon.messages.request import Request
from coapthon.utils import generate_random_token

__author__ = 'Giacomo Tanganelli'


class HelperClient(object):
    def __init__(self, server, sock=None):
        self.server = server
        self.protocol = CoAP(self.server, random.randint(1, 65535), self._wait_response, sock=sock)
        self.queue = Queue()

    def _wait_response(self, message):
        if message.code != defines.Codes.CONTINUE.number:
            self.queue.put(message)

    def stop(self):
        self.protocol.stopped.set()
        self.queue.put(None)
        self.protocol.close()

    def close(self):
        self.stop()

    def _thread_body(self, request, callback):
        self.protocol.send_message(request)
        while not self.protocol.stopped.isSet():
            response = self.queue.get(block=True)
            callback(response)

    def cancel_observing(self, response, send_rst):  # pragma: no cover
        if send_rst:
            message = Message()
            message.destination = self.server
            message.code = defines.Codes.EMPTY.number
            message.type = defines.Types["RST"]
            message.token = response.token
            message.mid = response.mid
            self.protocol.send_message(message)
        self.stop()

    def get(self, path, callback=None, timeout=None):  # pragma: no cover
        request = self.mk_request(defines.Codes.GET, path)

        return self.send_request(request, callback, timeout)

    def observe(self, path, callback, timeout=None):  # pragma: no cover
        request = self.mk_request(defines.Codes.GET, path)
        request.observe = 0

        return self.send_request(request, callback, timeout)

    def delete(self, path, callback=None, timeout=None):  # pragma: no cover
        request = self.mk_request(defines.Codes.DELETE, path)

        return self.send_request(request, callback, timeout)

    def post(self, path, payload, callback=None, timeout=None):  # pragma: no cover
        request = self.mk_request(defines.Codes.POST, path)
        request.token = generate_random_token(2)
        request.payload = payload

        return self.send_request(request, callback, timeout)

    def put(self, path, payload, callback=None, timeout=None):  # pragma: no cover
        request = self.mk_request(defines.Codes.PUT, path)
        request.payload = payload

        return self.send_request(request, callback, timeout)

    def discover(self, callback=None, timeout=None):  # pragma: no cover
        request = self.mk_request(defines.Codes.GET, defines.DISCOVERY_URL)

        return self.send_request(request, callback, timeout)

    def send_request(self, request, callback=None, timeout=None):  # pragma: no cover
        if callback is not None:
            thread = threading.Thread(target=self._thread_body, args=(request, callback))
            thread.start()
        else:
            self.protocol.send_message(request)
            response = self.queue.get(block=True, timeout=timeout)
            return response

    def send_empty(self, empty):  # pragma: no cover
        self.protocol.send_message(empty)

    def mk_request(self, method, path):
        request = Request()
        request.destination = self.server
        request.code = method.number
        request.uri_path = path
	return request
