import copy
import hashlib
import random
from threading import Timer
from coapthon import defines
from coapthon.client.coap_synchronous import HelperClientSynchronous
from coapthon.messages.message import Message
from coapthon.messages.request import Request
from coapthon.messages.response import Response
from coapthon.serializer import Serializer
from coapthon.server.coap_protocol import CoAP

__author__ = 'Giacomo Tanganelli'
__version__ = "2.0"


class ProxyCoAP(CoAP):
    def __init__(self, server_address, multicast=False):
        """
        Initialize the CoAP protocol

        """
        CoAP.__init__(self, server_address, multicast)
        self._forward = {}
        self._forward_mid = {}
        self._token = random.randint(1, 1000)
        self.timer = {}

    def finish_request(self, request, client_address):
       
        
        host = client_address[0]
        port = client_address[1]
        data = request[0]
        self.socket = request[1]
 
        # log.msg("Datagram received from " + str(host) + ":" + str(port))
        serializer = Serializer()
        message = serializer.deserialize(data, host, port)
        # print "Message received from " + host + ":" + str(port)
        # print "----------------------------------------"
        # print message
        # print "----------------------------------------"
        if isinstance(message, Request):
            # log.msg("Received request")
            ret = self.request_layer.handle_request(message)
            if isinstance(ret, Request):
                self.forward_request(ret)
        elif isinstance(message, Response):
            # log.err("Received response")
            rst = Message.new_rst(message)
            rst = self.message_layer.matcher_response(rst)
            # log.msg("Send RST")
            self.send(rst, host, port)
        elif isinstance(message, tuple):
            message, error = message
            response = Response()
            response.destination = (host, port)
            response.code = defines.responses[error]
            response = self.message_layer.reliability_response(message, response)
            response = self.message_layer.matcher_response(response)
            # log.msg("Send Error")
            self.send(response, host, port)
        elif message is not None:
            # ACK or RST
            # log.msg("Received ACK or RST")
            self.message_layer.handle_message(message)

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
        if uri is None:
            return self.send_error(request, response, "BAD_REQUEST")
        host, port, path = self.parse_path(uri)
        server = (str(host), int(port))
        token = self.generate_token()
        key = hash(str(host) + str(port) + str(token))
        to_store = copy.deepcopy(request)
        self._forward[key] = to_store
        # print request
        to_delete = []
        for option in request.options:
            if option.name == "Proxy-Uri" or not option.safe:
                to_delete.append(option)

        for option in to_delete:
            request.del_option(option)

        client = HelperClientSynchronous()
        self._currentMID += 1
        client.starting_mid = self._currentMID % (1 << 16)
        method = defines.codes[request.code]
        if method == 'GET':
            function = client.get
            req = copy.deepcopy(request)
            req.destination = server
            req.uri_path = path
            req.token = str(token)

        elif method == 'POST':
            function = client.post
            req = copy.deepcopy(request)
            req.destination = server
            req.uri_path = path
            req.token = str(token)

        elif method == 'PUT':
            function = client.put
            req = copy.deepcopy(request)
            req.destination = server
            req.uri_path = path
            req.token = str(token)

        elif method == 'DELETE':
            function = client.delete
            req = copy.deepcopy(request)
            req.destination = server
            req.uri_path = path
            req.token = str(token)

        else:
            return self.send_error(to_store, response, "BAD_REQUEST")
        req.source = None
        args = (req,)

        key = hash(str(host) + str(port) + str((client.starting_mid + 1) % (1 << 16)))
        self._forward_mid[key] = req
        # Render_GET
        with ThreadPoolExecutor(max_workers=100) as executor:
            self.timer[request.mid] = executor.submit(self.send_delayed_ack, request)
        # with ThreadPoolExecutor(max_workers=100) as executor:
        #     future = executor.submit(client.start, [(function, args, {})])
        #     future.add_done_callback(self.result_forward)
        # print req
        operations = [(function, args, {})]
        function, args, kwargs = operations[0]
        response = function(*args, **kwargs)
        self.result_forward(response=response)
        return None

    def send_delayed_ack(self, request):
        time.sleep(defines.SEPARATE_TIMEOUT)
        self.send_ack([request])

    def send_ack(self, list_request):
        """
        Send an ack to the client. Used mostly with separate.

        :param list_request: the request to be acknowledge.
        :type list_request: [Request] or Request
        """

        if isinstance(list_request, list):
            request = list_request[0]
        else:
            request = list_request
        del self.timer[request.mid]
        host, port = request.source
        ack = Message.new_ack(request)
        self.send(ack, host, port)

    def result_forward(self, future=None, response=None):
        """
        Forward results to the client.

        :param future: the future object.
        """
        if future is not None:
            print future
            print future.result()
            response = future.result()
        host, port = response.source
        key = hash(str(host) + str(port) + str(response.token))
        request = self._forward.get(key)
        if request.mid in self.timer and self.timer[request.mid].cancel():
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

            del self._forward[key]
            host, port = response.source
            key = hash(str(host) + str(port) + str(response.mid))
            try:
                del self._forward_mid[key]
            except KeyError:
                # log.err("MID has not been deleted")
                pass
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
                # log.err("MID has not been deleted")
                pass
            self.send(response, host, port)