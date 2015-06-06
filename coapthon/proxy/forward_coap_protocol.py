import hashlib
import os
import random
import re
from threading import Timer
from twisted.application.service import Application
from twisted.python import log
from twisted.python.log import ILogObserver, FileLogObserver
from twisted.python.logfile import DailyLogFile
from coapthon import defines
from coapthon.client.coap_protocol import HelperClient
from coapthon.messages.message import Message
from coapthon.messages.request import Request
from coapthon.messages.response import Response
from coapthon.serializer import Serializer
from coapthon.server.coap_protocol import CoAP

__author__ = 'Giacomo Tanganelli'
__version__ = "2.0"


home = os.path.expanduser("~")
if not os.path.exists(home + "/.coapthon/"):
    os.makedirs(home + "/.coapthon/")

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
        self._forward_mid = {}
        self._token = random.randint(1, 1000)
        self.timer = None

    def startProtocol(self):
        """
        Called after protocol has started listening.
        """
        # Set the TTL>1 so multicast will cross router hops:
        # self.transport.setTTL(5)
        # Join a specific multicast group:
        # self.transport.joinGroup(defines.ALL_COAP_NODES)

    def datagramReceived(self, data, addr):
        """
        Handler for received dUDP datagram.

        :param data: the UDP datagram
        :param host: source host
        :param port: source port
        """
        try:
            host, port = addr
        except ValueError:
            host, port , tmp1, tmp2 = addr
        log.msg("Datagram received from " + str(host) + ":" + str(port))
        serializer = Serializer()
        message = serializer.deserialize(data, host, port)
        # print "Message received from " + host + ":" + str(port)
        # print "----------------------------------------"
        # print message
        # print "----------------------------------------"
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

    def parse_path(self, path):
        return self.parse_path_ipv6(path)
        # m = re.match("([a-zA-Z]{4,5})://([a-zA-Z0-9.]*):([0-9]*)/(\S*)", path)
        # if m is None:
        #     m = re.match("([a-zA-Z]{4,5})://([a-zA-Z0-9.]*)/(\S*)", path)
        #     if m is None:
        #         m = re.match("([a-zA-Z]{4,5})://([a-zA-Z0-9.]*)", path)
        #         if m is None:
        #             ip, port, path = self.parse_path_ipv6(path)
        #         else:
        #             ip = m.group(2)
        #             port = 5683
        #             path = ""
        #     else:
        #         ip = m.group(2)
        #         port = 5683
        #         path = m.group(3)
        # else:
        #     ip = m.group(2)
        #     port = int(m.group(3))
        #     path = m.group(4)
        #
        # return ip, port, path

    @staticmethod
    def parse_path_ipv6(path):
        m = re.match("([a-zA-Z]{4,5})://\[([a-fA-F0-9:]*)\]:([0-9]*)/(\S*)", path)
        if m is None:
            m = re.match("([a-zA-Z]{4,5})://\[([a-fA-F0-9:]*)\]/(\S*)", path)
            if m is None:
                m = re.match("([a-zA-Z]{4,5})://\[([a-fA-F0-9:]*)\]", path)
                ip = m.group(2)
                port = 5683
                path = ""
            else:
                ip = m.group(2)
                port = 5683
                path = m.group(3)
        else:
            ip = m.group(2)
            port = int(m.group(3))
            path = m.group(4)

        return ip, port, path

    def forward_request(self, request):
        """
        Forward an incoming request to the specified server.

        :param request: the request to be forwarded
        :return: None if success, send an error otherwise
        """
        uri = request.proxy_uri
        response = Response()
        response.destination = request.source
        token = self.generate_token()
        if uri is None:
            return self.send_error(request, response, "BAD_REQUEST")
        host, port, path = self.parse_path(uri)
        server = (str(host), int(port))
        request.uri_path = path
        client = HelperClient(server, True)
        self._currentMID += 1
        client.starting_mid = self._currentMID % (1 << 16)
        method = defines.codes[request.code]
        if method == 'GET':
            function = client.protocol.get
            args = (path,)
            kwargs = {"Token": str(token), "MID": self._currentMID % (1 << 16)}
            callback = self.result_forward
            err_callback = self.error
        elif method == 'POST':
            function = client.protocol.post
            args = (path, request.payload)
            kwargs = {"Token": str(token), "MID": self._currentMID % (1 << 16)}
            callback = self.result_forward
            err_callback = self.error
        elif method == 'PUT':
            function = client.protocol.put
            args = (path, request.payload)
            kwargs = {"Token": str(token), "MID": self._currentMID % (1 << 16)}
            callback = self.result_forward
            err_callback = self.error
        elif method == 'DELETE':
            function = client.protocol.delete
            args = (path,)
            kwargs = {"Token": str(token), "MID": self._currentMID % (1 << 16)}
            callback = self.result_forward
            err_callback = self.error
        else:
            return self.send_error(request, response, "BAD_REQUEST")
        for option in request.options:
            if option.safe:
                kwargs[option.name] = option.value

        operations = [(function, args, kwargs, (callback, err_callback))]
        key = hash(str(host) + str(port) + str(token))
        self._forward[key] = request
        key = hash(str(host) + str(port) + str(self._currentMID % (1 << 16)))
        self._forward_mid[key] = request
        client.start(operations)
        # Render_GET
        # self.timer = Timer(defines.SEPARATE_TIMEOUT, self.send_ack, [request])
        # self.timer.start()
        return None

    def send_ack(self, list_request):
        """
        Send an ack to the client. Used mostly with separate.

        :param list_request: the request to be acknowledge.
        :type list_request: [Request] or Request
        """
        self.timer = None
        if isinstance(list_request, list):
            request = list_request[0]
        else:
            request = list_request
        host, port = request.source
        ack = Message.new_ack(request)
        self.send(ack, host, port)

    def result_forward(self, response, request=None):
        """
        Forward results to the client.

        :param response: the response sent by the server.
        """
        print "FORWARD"
        skip_delete = False
        host, port = response.source
        key_mid = hash(str(host) + str(port) + str(response.mid))
        key = None
        if request is None:
            host, port = response.source
            key = hash(str(host) + str(port) + str(response.token))
            request = self._forward.get(key)
        else:
            skip_delete = True
        # print request
        if self.timer is not None:
            self.timer.cancel()
            response.type = defines.inv_types["ACK"]
            response.mid = request.mid
        elif skip_delete:
            response.type = defines.inv_types["ACK"]
            response.mid = request.mid
        else:
            if request.type == defines.inv_types["CON"]:
                response.type = defines.inv_types["CON"]
            else:
                response.type = defines.inv_types["NON"]

        if request is not None:
            response.destination = request.source
            response.token = request.token
            if not skip_delete:
                del self._forward[key]
                try:
                    del self._forward_mid[key_mid]
                except KeyError:
                    log.err("MID has not been deleted")
            host, port = request.source
            if response.mid is None:
                response.mid = self._currentMID
            self.send(response, host, port)

    def generate_token(self):
        """
        Generate tokens.

        :return: a token.
        """
        self._token += 1
        # md5 = hashlib.md5()
        # md5.update(str(self._token))
        # token = md5.digest()
        # return token[0:15]
        return str(self._token)

    def error(self, mid, host, port):
        """
        Handler of errors. Send an error message to the client.

        :param mid: the mid of the response that generates the error.
        :param host: the host of the server.
        :param port: the port of the server.
        """
        key = hash(str(host) + str(port) + str(mid))
        request = self._forward_mid.get(key)
        if request is not None:
            response = Response()
            host, port = request.source
            response.destination = request.source
            response.token = request.token
            response._mid = self._currentMID
            response.type = defines.inv_types["NON"]
            response.code = defines.responses["GATEWAY_TIMEOUT"]
            key = hash(str(host) + str(port) + str(response.token))
            del self._forward[key]
            key = hash(str(host) + str(port) + str(mid))
            try:
                del self._forward_mid[key]
            except KeyError:
                log.err("MID has not been deleted")
            self.send(response, host, port)