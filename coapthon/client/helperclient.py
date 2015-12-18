import random
from multiprocessing import Queue
import threading
from coapthon.messages.message import Message
from coapthon import defines
from coapthon.client.coap import CoAP
from coapthon.messages.request import Request
from coapthon.utils import generate_random_token

__author__ = 'jacko'


class HelperClient(object):
    def __init__(self, server):
        self.server = server
        self.protocol = CoAP(self.server, random.randint(1, 65535), self._wait_response)
        self.queue = Queue()

    def _wait_response(self, message):
        if message.code != defines.Codes.CONTINUE.number:
            self.queue.put(message)

    def stop(self):
        self.protocol.stopped.set()
        self.queue.put(None)

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

    def get(self, path, callback=None):  # pragma: no cover
        request = Request()
        request.destination = self.server
        request.code = defines.Codes.GET.number
        request.uri_path = path

        if callback is not None:
            thread = threading.Thread(target=self._thread_body, args=(request, callback))
            thread.start()
        else:
            self.protocol.send_message(request)
            response = self.queue.get(block=True)
            return response

    def observe(self, path, callback):  # pragma: no cover
        request = Request()
        request.destination = self.server
        request.code = defines.Codes.GET.number
        request.uri_path = path
        request.observe = 0

        if callback is not None:
            thread = threading.Thread(target=self._thread_body, args=(request, callback))
            thread.start()
        else:
            self.protocol.send_message(request)
            response = self.queue.get(block=True)
            return response

    def delete(self, path, callback=None):  # pragma: no cover
        request = Request()
        request.destination = self.server
        request.code = defines.Codes.DELETE.number
        request.uri_path = path
        if callback is not None:
            thread = threading.Thread(target=self._thread_body, args=(request, callback))
            thread.start()
        else:
            self.protocol.send_message(request)
            response = self.queue.get(block=True)
            return response

    def post(self, path, payload, callback=None):  # pragma: no cover
        request = Request()
        request.destination = self.server
        request.code = defines.Codes.POST.number
        request.token = generate_random_token(2)
        request.uri_path = path
        request.payload = payload
        if callback is not None:
            thread = threading.Thread(target=self._thread_body, args=(request, callback))
            thread.start()
        else:
            self.protocol.send_message(request)
            response = self.queue.get(block=True)
            return response

    def put(self, path, payload, callback=None):  # pragma: no cover
        request = Request()
        request.destination = self.server
        request.code = defines.Codes.PUT.number
        request.uri_path = path
        request.payload = payload
        if callback is not None:
            thread = threading.Thread(target=self._thread_body, args=(request, callback))
            thread.start()
        else:
            self.protocol.send_message(request)
            response = self.queue.get(block=True)
            return response

    def discover(self, callback=None):  # pragma: no cover
        request = Request()
        request.destination = self.server
        request.code = defines.Codes.GET.number
        request.uri_path = defines.DISCOVERY_URL
        if callback is not None:
            thread = threading.Thread(target=self._thread_body, args=(request, callback))
            thread.start()
        else:
            self.protocol.send_message(request)
            response = self.queue.get(block=True)
            return response

    def send_request(self, request, callback=None):  # pragma: no cover
        if callback is not None:
            thread = threading.Thread(target=self._thread_body, args=(request, callback))
            thread.start()
        else:
            self.protocol.send_message(request)
            response = self.queue.get(block=True)
            return response

    def send_empty(self, empty):  # pragma: no cover
        self.protocol.send_message(empty)