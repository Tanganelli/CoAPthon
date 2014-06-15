import hashlib
import random
from threading import Timer
from twisted.application.service import Application
from twisted.python import log
from twisted.python.log import ILogObserver, FileLogObserver
from twisted.python.logfile import DailyLogFile
from coapthon2 import defines
from coapthon2.client.coap_protocol import HelperClient
from coapthon2.messages.message import Message
from coapthon2.messages.request import Request
from coapthon2.messages.response import Response
from coapthon2.serializer import Serializer
from coapthon2.server.coap_protocol import CoAP

__author__ = 'Giacomo Tanganelli'
__version__ = "2.0"

from os.path import expanduser
home = expanduser("~")

logfile = DailyLogFile("CoAPthon_forward_proxy.log", home + "/.coapthon/")
# Now add an observer that logs to a file
application = Application("CoAPthon_Forward_Proxy")
application.setComponent(ILogObserver, FileLogObserver(logfile).emit)


class ProxyCoAP(CoAP):
    def __init__(self):
        """
        Initialize the CoAP protocol

        """
        CoAP.__init__(self)
        self._forward = {}
        self._token = random.randint(1, 1000)
        self.timer = None

    def datagramReceived(self, data, (host, port)):
        """
        Handler for received dUDP datagram.

        :param data: the UDP datagram
        :param host: source host
        :param port: source port
        """
        log.msg("Datagram received from " + str(host) + ":" + str(port))
        serializer = Serializer()
        message = serializer.deserialize(data, host, port)
        print "Message received from " + host + ":" + str(port)
        print "----------------------------------------"
        print message
        print "----------------------------------------"
        if isinstance(message, Request):
            log.msg("Received request")
            ret = self._request_layer.handle_request(message)
            if isinstance(ret, Request):
                self.forward_request(ret)
            else:
                return
        elif isinstance(message, Response):
            log.err("Received response")
            rst = Message.new_rst(message)
            rst = self._message_layer.matcher_response(rst)
            log.msg("Send RST")
            self.send(rst, host, port)
        elif isinstance(message, tuple):
            message, error = message
            response = Response()
            response.destination = (host, port)
            response.code = defines.responses[error]
            response = self.reliability_response(message, response)
            response = self._message_layer.matcher_response(response)
            log.msg("Send Error")
            self.send(response, host, port)
        elif message is not None:
            # ACK or RST
            log.msg("Received ACK or RST")
            self._message_layer.handle_message(message)

    def forward_request(self, request):
        uri = request.proxy_uri
        response = Response()
        response.destination = request.source
        token = self.generate_token()
        if uri is None:
            return self.send_error(request, response, "BAD_REQUEST")
        schema = uri.split("://")
        try:
            path = schema[1]
            schema = schema[0]
            host_pos = path.index("/")
            destination = path[:host_pos]
            destination = destination.split(":")
            port = 5683
            host = destination[0]
            if len(destination) > 1:
                port = int(destination[1])
            path = path[host_pos:]
            server = (host, port)
        except IndexError:
            return self.send_error(request, response, "BAD_REQUEST")
        request.uri_path = path
        client = HelperClient(server, True)
        self._currentMID += 1
        client.starting_mid = self._currentMID % (1 << 16)
        method = defines.codes[request.code]
        if method == 'GET':
            function = client.protocol.get
            args = (path,)
            kwargs = {"Token": str(token)}
            callback = self.result_forward
        elif method == 'POST':
            function = client.protocol.post
            args = (path, request.payload)
            kwargs = {"Token": str(token)}
            callback = self.result_forward
        elif method == 'PUT':
            function = client.protocol.put
            args = (path, request.payload)
            kwargs = {"Token": str(token)}
            callback = self.result_forward
        elif method == 'DELETE':
            function = client.protocol.delete
            args = (path,)
            kwargs = {"Token": str(token)}
            callback = self.result_forward
        else:
            return self.send_error(request, response, "BAD_REQUEST")
        operations = [(function, args, kwargs, callback)]
        key = hash(str(host) + str(port) + str(token))
        self._forward[key] = request
        client.start(operations)
        # Render_GET
        self.timer = Timer(defines.SEPARATE_TIMEOUT, self.send_ack, [request])
        self.timer.start()
        return None

    def send_ack(self, list_request):
        self.timer = None
        request = list_request[0]
        host, port = request.source
        ack = Message.new_ack(request)
        self.send(ack, host, port)

    def result_forward(self, response):
        host, port = response.source
        key = hash(str(host) + str(port) + str(response.token))
        request = self._forward.get(key)
        if self.timer is not None:
            self.timer.cancel()
            response.type = defines.inv_types["ACK"]
            response.mid = request.mid
        else:
            if request.type == defines.inv_types["CON"]:
                response.type = defines.inv_types["CON"]
            else:
                response.type = defines.inv_types["NON"]
            response.mid = self._currentMID

        if request is not None:
            host, port = request.source
            response.destination = request.source
            response.token = request.token
            del self._forward[key]
            self.send(response, host, port)

    def generate_token(self):
        self._token += 1
        md5 = hashlib.md5()
        md5.update(str(self._token))
        token = md5.digest()
        return token[0:15]