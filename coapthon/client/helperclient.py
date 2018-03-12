import random
import threading
from coapthon.messages.message import Message
from coapthon import defines
from coapthon.client.coap import CoAP
from coapthon.messages.request import Request
from coapthon.utils import generate_random_token

__author__ = 'Giacomo Tanganelli'

class _RequestContext(object):
    def __init__(self, request, callback=None):
        self.request = request
        if callback:
            self.callback = callback
        else:
            self.response = None
            self.responded = threading.Event()

class HelperClient(object):
    """
    Helper Client class to perform requests to remote servers in a simplified way.
    """
    def __init__(self, server, sock=None, cb_ignore_read_exception=None, cb_ignore_write_exception=None):
        """
        Initialize a client to perform request to a server.

        :param server: the remote CoAP server
        :param sock: if a socket has been created externally, it can be used directly
        :param cb_ignore_read_exception: Callback function to handle exception raised during the socket read operation
        :param cb_ignore_write_exception: Callback function to handle exception raised during the socket write operation 
        """
        self.server = server
        self.protocol = CoAP(self.server, random.randint(1, 65535), self._wait_response, sock=sock,
                             cb_ignore_read_exception=cb_ignore_read_exception, cb_ignore_write_exception=cb_ignore_write_exception)

        self.requests_lock = threading.RLock()
        self.requests = dict()

    def _wait_response(self, message):
        """
        Private function to get responses from the server.

        :param message: the received message
        """
        if message.code == defines.Codes.CONTINUE.number:
            return
        with self.requests_lock:
            if message.token not in self.requests:
                return
            context = self.requests[message.token]
            if message.timeouted:
                # Message is actually the original timed out request (not the response), discard content
                message = None
            if hasattr(context, 'callback'):
                if not hasattr(context.request, 'observe'):
                    # OBSERVE stays until cancelled, for all others we're done
                    del self.requests[message.token]
                context.callback(message)
            else:
                # Signal that a response is available to blocking call
                context.response = message
                context.responded.set()

    def stop(self):
        """
        Stop the client.
        """
        self.protocol.close()
        with self.requests_lock:
            # Unblock/signal waiters
            for token in self.requests:
                context = self.requests[token]
                if hasattr(context, 'callback'):
                    context.callback(None)
                else:
                    context.responded.set()

    def close(self):
        """
        Close the client.
        """
        self.stop()

    def cancel_observe_token(self, token, explicit, timeout=None):  # pragma: no cover
        """
        Delete observing on the remote server.

        :param token: the observe token
        :param explicit: if explicitly cancel
        :type explicit: bool
        """
        with self.requests_lock:
            if token not in self.requests:
                return
            if not hasattr(self.requests[token].request, 'observe'):
                return
            context = self.requests[token]
            del self.requests[token]

        self.protocol.end_observation(token)

        if not explicit:
            return

        request = self.mk_request(defines.Codes.GET, context.request.uri_path)

        # RFC7641 explicit cancel is by sending OBSERVE=1 with the same token,
        # not by an unsolicited RST (which would be ignored)
        request.token = token
        request.observe = 1

        self.send_request(request, callback=None, timeout=timeout)
        
    def cancel_observing(self, response, explicit):  # pragma: no cover
        """
        Delete observing on the remote server.

        :param response: the last received response
        :param explicit: if explicitly cancel using token
        :type send_rst: bool
        """
        self.cancel_observe_token(self, response.token, explicit)

    def get(self, path, callback=None, timeout=None, **kwargs):  # pragma: no cover
        """
        Perform a GET on a certain path.

        :param path: the path
        :param callback: the callback function to invoke upon response
        :param timeout: the timeout of the request
        :return: the response
        """
        request = self.mk_request(defines.Codes.GET, path)
        request.token = generate_random_token(2)

        for k, v in kwargs.iteritems():
            if hasattr(request, k):
                setattr(request, k, v)

        return self.send_request(request, callback, timeout)

    def observe(self, path, callback, timeout=None, **kwargs):  # pragma: no cover
        """
        Perform a GET with observe on a certain path.

        :param path: the path
        :param callback: the callback function to invoke upon notifications
        :param timeout: the timeout of the request
        :return: the response to the observe request
        """
        request = self.mk_request(defines.Codes.GET, path)
        request.token = generate_random_token(2)
        request.observe = 0

        for k, v in kwargs.iteritems():
            if hasattr(request, k):
                setattr(request, k, v)

        return self.send_request(request, callback, timeout)

    def delete(self, path, callback=None, timeout=None, **kwargs):  # pragma: no cover
        """
        Perform a DELETE on a certain path.

        :param path: the path
        :param callback: the callback function to invoke upon response
        :param timeout: the timeout of the request
        :return: the response
        """
        request = self.mk_request(defines.Codes.DELETE, path)
        request.token = generate_random_token(2)

        for k, v in kwargs.iteritems():
            if hasattr(request, k):
                setattr(request, k, v)

        return self.send_request(request, callback, timeout)

    def post(self, path, payload, callback=None, timeout=None, **kwargs):  # pragma: no cover
        """
        Perform a POST on a certain path.

        :param path: the path
        :param payload: the request payload
        :param callback: the callback function to invoke upon response
        :param timeout: the timeout of the request
        :return: the response
        """
        request = self.mk_request(defines.Codes.POST, path)
        request.token = generate_random_token(2)
        request.payload = payload

        for k, v in kwargs.iteritems():
            if hasattr(request, k):
                setattr(request, k, v)

        return self.send_request(request, callback, timeout)

    def put(self, path, payload, callback=None, timeout=None, **kwargs):  # pragma: no cover
        """
        Perform a PUT on a certain path.

        :param path: the path
        :param payload: the request payload
        :param callback: the callback function to invoke upon response
        :param timeout: the timeout of the request
        :return: the response
        """
        request = self.mk_request(defines.Codes.PUT, path)
        request.token = generate_random_token(2)
        request.payload = payload

        for k, v in kwargs.iteritems():
            if hasattr(request, k):
                setattr(request, k, v)

        return self.send_request(request, callback, timeout)

    def discover(self, callback=None, timeout=None, **kwargs):  # pragma: no cover
        """
        Perform a Discover request on the server.

        :param callback: the callback function to invoke upon response
        :param timeout: the timeout of the request
        :return: the response
        """
        request = self.mk_request(defines.Codes.GET, defines.DISCOVERY_URL)
        request.token = generate_random_token(2)

        for k, v in kwargs.iteritems():
            if hasattr(request, k):
                setattr(request, k, v)

        return self.send_request(request, callback, timeout)

    def send_request(self, request, callback=None, timeout=None):  # pragma: no cover
        """
        Send a request to the remote server.

        :param request: the request to send
        :param callback: the callback function to invoke upon response
        :param timeout: the timeout of the request
        :return: the response (synchronous), or the token (for asynchronous callback)
        """

        with self.requests_lock:
            # Same requests from the same endpoint must have different tokens
            # Ensure there is a unique token in case the other side issues a
            # delayed response after a standalone ACK
            while request.token in self.requests:
                request.token = generate_random_token(2)
            context = _RequestContext(request, callback)
            self.requests[request.token] = context
        self.protocol.send_message(request)
        if callback:
            # So that requester can cancel asynchronous OBSERVE
            return request.token

        # Wait for response
        context.responded.wait(timeout)
        del self.requests[request.token]
        return context.response


    def send_empty(self, empty):  # pragma: no cover
        """
        Send empty message.

        :param empty: the empty message
        """
        self.protocol.send_message(empty)

    def mk_request(self, method, path):
        """
        Create a request.

        :param method: the CoAP method
        :param path: the path of the request
        :return:  the request
        """
        request = Request()
        request.destination = self.server
        request.code = method.number
        request.uri_path = path
        return request


