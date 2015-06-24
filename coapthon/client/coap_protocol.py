import os
import random
import re
import time
import twisted
from twisted.application.service import Application
from twisted.internet.error import AlreadyCancelled
from twisted.python import log
from twisted.python.log import ILogObserver, FileLogObserver
from twisted.python.logfile import DailyLogFile
from coapthon import defines
from coapthon.messages.message import Message
from coapthon.messages.option import Option
from coapthon.messages.request import Request
from coapthon.messages.response import Response
from coapthon.resources.resource import Resource
from coapthon.serializer import Serializer
from twisted.internet import task
from coapthon.utils import Tree
from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor

__author__ = 'Giacomo Tanganelli'
__version__ = "2.0"


home = os.path.expanduser("~")
if not os.path.exists(home + "/.coapthon/"):
    os.makedirs(home + "/.coapthon/")

# First, startLogging to capture stdout
logfile = DailyLogFile("CoAPthon_client.log", home + "/.coapthon/")
# Now add an observer that logs to a file
application = Application("CoAPthon_Client")
application.setComponent(ILogObserver, FileLogObserver(logfile).emit)


class CoAP(DatagramProtocol):
    def __init__(self, server, forward):
        # print "INIT CLIENT\n"
        self._forward = forward
        self.received = {}
        self.sent = {}
        self.sent_token = {}
        self.received_token = {}
        self.call_id = {}
        self.relation = {}
        self._currentMID = 1
        import socket
        try:
            socket.inet_aton(server[0])
            self.server = server
            # legal
        except socket.error:
            # Not legal
            data = socket.getaddrinfo(server[0], server[1])

            self.server = (server[0], server[1])

        # defer = reactor.resolve('coap.me')
        # defer.addCallback(self.start)
        # self.server = (None, 5683)

        root = Resource('root', visible=False, observable=False, allow_children=True)
        root.path = '/'
        self.root = Tree()
        self.root["/"] = root
        self.operations = []
        self.l = None


    @property
    def current_mid(self):
        return self._currentMID

    @current_mid.setter
    def current_mid(self, c):
        self._currentMID = c

    def set_operations(self, operations):
        for op in operations:
            function, args, kwargs, client_callback = op
            self.operations.append((function, args, kwargs, client_callback))
        host, port = self.server

        if host is not None:
            self.start(host)

    def startProtocol(self):
        # print "STARTPROTOCOL\n"
        # self.transport.connect(self.server)
        if self.server is None:
            log.err("Server address for the client is not initialized")
            exit()
        self.l = task.LoopingCall(self.purge_mids)
        self.l.start(defines.EXCHANGE_LIFETIME)

    def stopProtocol(self):
        self.l.stop()

    def purge_mids(self):
        log.msg("Purge mids")
        now = time.time()
        sent_key_to_delete = []
        for key in self.sent.keys():
            message, timestamp, callback, client_callback = self.sent.get(key)
            if timestamp + defines.EXCHANGE_LIFETIME <= now:
                sent_key_to_delete.append(key)
        for key in sent_key_to_delete:
            message, timestamp, callback, client_callback = self.sent.get(key)
            key_token = hash(str(self.server[0]) + str(self.server[1]) + str(message.token))
            try:
                del self.sent[key]
            except KeyError:
                pass
            try:
                del self.received[key]
            except KeyError:
                pass
            try:
                del self.sent_token[key_token]
            except KeyError:
                pass
            try:
                del self.received_token[key_token]
            except KeyError:
                pass

    def start(self, host):
        # print "START\n"
        # self.transport.connect(host, self.server[1])
        function, args, kwargs, client_callback = self.get_operation()
        function(client_callback, *args, **kwargs)

    # def start_test(self, transport):
    #     self.transport = transport
    #     function, args, kwargs, client_callback = self.get_operation()
    #     function(client_callback, *args, **kwargs)

    def get_operation(self):
        try:
            to_exec = self.operations.pop(0)
            args = []
            kwargs = {}
            if len(to_exec) == 4:
                function, args, kwargs, client_callback = to_exec
            elif len(to_exec) == 3:
                function, args, client_callback = to_exec
            elif len(to_exec) == 2:
                function, client_callback = to_exec[0]
            else:
                return None, None, None, None
            return function, args, kwargs, client_callback
        except IndexError:
            return None, None, None, None

    def send(self, message):
        # print "SEND\n"
        serializer = Serializer()
        if message.destination is None:
            message.destination = self.server
        host, port = message.destination
        print "Message sent to " + host + ":" + str(port)
        print "----------------------------------------"
        print message
        print "----------------------------------------"
        datagram = serializer.serialize(message)
        log.msg("Send datagram")
        self.transport.write(datagram, message.destination)

    def send_callback(self, req, callback, client_callback):
        if req.mid is None:
            self._currentMID += 1
            req.mid = self._currentMID
        key = hash(str(self.server[0]) + str(self.server[1]) + str(req.mid))
        key_token = hash(str(self.server[0]) + str(self.server[1]) + str(req.token))
        self.sent[key] = (req, time.time(), callback, client_callback)
        self.sent_token[key_token] = (req, time.time(), callback, client_callback)
        if isinstance(client_callback, tuple) and len(client_callback) > 1:
            client_callback, err_callback = client_callback
        else:
            err_callback = None
        self.schedule_retrasmission(req, err_callback)
        self.send(req)

    def datagramReceived(self, datagram, host):
        # print "RECEIVED\n"
        serializer = Serializer()
        try:
            host, port = host
        except ValueError:
            host, port, tmp1, tmp2 = host
        message = serializer.deserialize(datagram, host, port)

        print "Message received from " + host + ":" + str(port)
        print "----------------------------------------"
        print message
        print "----------------------------------------"
        if isinstance(message, Response):
            self.handle_response(message)
        elif isinstance(message, Request):
            log.err("Received request")
        else:
            self.handle_message(message)

        key = hash(str(host) + str(port) + str(message.mid))
        if message.type == defines.inv_types["ACK"] and message.code == defines.inv_codes["EMPTY"] \
           and key in self.sent.keys():
            # Separate Response
            print "Separate Response"
        else:
            function, args, kwargs, client_callback = self.get_operation()
            key = hash(str(host) + str(port) + str(message.token))
            if function is None and len(self.relation) == 0:
                if not self._forward:
                    reactor.stop()
            elif key in self.relation:
                response, timestamp, client_callback = self.relation.get(key)
                self.handle_notification(message, client_callback)
            else:
                function(client_callback, *args, **kwargs)

    def handle_message(self, message):
        host, port = message.source
        key = hash(str(host) + str(port) + str(message.mid))
        if message.type == defines.inv_types["ACK"] and message.code == defines.inv_codes["EMPTY"] \
           and key in self.sent.keys():
            return None
        if key in self.sent.keys():
            self.received[key] = message
            if message.type == defines.inv_types["RST"]:
                print message
            else:
                req, timestamp, callback, client_callback = self.sent[key]
                callback(message.mid, client_callback)

    def handle_response(self, response):
        if response.type == defines.inv_types["CON"]:
            ack = Message.new_ack(response)
            self.send(ack)
        key_token = hash(str(self.server[0]) + str(self.server[1]) + str(response.token))

        if key_token in self.sent_token.keys():
            self.received_token[key_token] = response
            req, timestamp, callback, client_callback = self.sent_token[key_token]
            key = hash(str(self.server[0]) + str(self.server[1]) + str(req.mid))
            self.received[key] = response
            callback(req.mid, client_callback)

    def discover(self, client_callback, *args, **kwargs):
        req = Request()
        if "Token" in kwargs.keys():
            req.token = kwargs.get("Token")
        if "MID" in kwargs.keys():
            req.mid = kwargs.get("MID")
        if "Server" in kwargs.keys():
            req.destination = kwargs.get("Server")
            del kwargs["Server"]
        req.code = defines.inv_codes['GET']
        req.uri_path = ".well-known/core"
        req.type = defines.inv_types["CON"]
        self.send_callback(req, self.discover_results, client_callback)

    def discover_results(self, mid, client_callback):
        key = hash(str(self.server[0]) + str(self.server[1]) + str(mid))
        response = self.received.get(key)
        if key in self.call_id.keys():
            handler, retransmit_count = self.call_id.get(key)
            if handler is not None:
                try:
                    log.msg("Cancel retrasmission")
                    handler.cancel()
                except AlreadyCancelled:
                    pass
        err_callback = None
        if isinstance(client_callback, tuple) and len(client_callback) > 1:
            client_callback, err_callback = client_callback
        elif isinstance(client_callback, tuple):
            client_callback = client_callback[0]
        if response is not None:
            # self.parse_core_link_format(response.payload)
            client_callback(response)
        elif err_callback is not None:
            err_callback(mid, self.server[0], self.server[1])

    def get(self, client_callback, *args, **kwargs):
        # print "GET\n"
        if isinstance(args[0], str):
            path = str(args[0])
            req = Request()
            req.uri_path = path
            if "Token" in kwargs.keys():
                req.token = kwargs.get("Token")
                del kwargs["Token"]
            if "MID" in kwargs.keys():
                req.mid = kwargs.get("MID")
                del kwargs["MID"]
            if "Server" in kwargs.keys():
                req.destination = kwargs.get("Server")
                del kwargs["Server"]
        else:
            req = args[0]
        for key in kwargs:
            try:
                o = Option()
                o.number = defines.inv_options[key]
                o.value = kwargs[key]
                req.add_option(o)
            except KeyError:
                pass

        req.code = defines.inv_codes['GET']
        req.type = defines.inv_types["CON"]
        self.send_callback(req, self.get_results, client_callback)

    def get_results(self, mid, client_callback):
        key = hash(str(self.server[0]) + str(self.server[1]) + str(mid))
        response = self.received.get(key)
        if key in self.call_id.keys():
            handler, retransmit_count = self.call_id.get(key)
            if handler is not None:
                try:
                    log.msg("Cancel retrasmission")
                    handler.cancel()
                except AlreadyCancelled:
                    pass

        err_callback = None
        if isinstance(client_callback, tuple) and len(client_callback) > 1:
            client_callback, err_callback = client_callback
        elif isinstance(client_callback, tuple):
            client_callback = client_callback[0]
        if response is not None:
            # self.parse_core_link_format(response.payload)
            client_callback(response)
        elif err_callback is not None:
            err_callback(mid, self.server[0], self.server[1])

    def observe(self, client_callback, *args, **kwargs):
        if isinstance(args[0], str):
            path = str(args[0])
            req = Request()
            req.uri_path = path
            if "Token" in kwargs.keys():
                req.token = kwargs.get("Token")
                del kwargs["Token"]
            if "MID" in kwargs.keys():
                req.mid = kwargs.get("MID")
                del kwargs["MID"]
            if "Server" in kwargs.keys():
                req.destination = kwargs.get("Server")
                del kwargs["Server"]
        else:
            req = args[0]
            assert(isinstance(req, Request))
            path = req.uri_path
        for key in kwargs:
            try:
                o = Option()
                o.number = defines.inv_options[key]
                o.value = kwargs[key]
                req.add_option(o)
            except KeyError:
                pass

        req.code = defines.inv_codes['GET']
        req.uri_path = path
        req.observe = 0
        req.type = defines.inv_types["CON"]
        self.send_callback(req, self.observe_results, client_callback)

    def observe_results(self, mid, client_callback):
        key = hash(str(self.server[0]) + str(self.server[1]) + str(mid))
        response = self.received.get(key)
        if key in self.call_id.keys():
            handler, retransmit_count = self.call_id.get(key)
            if handler is not None:
                try:
                    log.msg("Cancel retrasmission")
                    handler.cancel()
                except AlreadyCancelled:
                    pass

        err_callback = None
        if isinstance(client_callback, tuple) and len(client_callback) > 1:
            client_callback, err_callback = client_callback
        elif isinstance(client_callback, tuple):
            client_callback = client_callback[0]
        if response is not None:
            if response.observe != 0:
                # TODO add observing results
                host, port = response.source
                key = hash(str(host) + str(port) + str(response.token))
                self.relation[key] = (response, time.time(), client_callback)
            client_callback(response)
        elif err_callback is not None:
            err_callback(mid, self.server[0], self.server[1])

    def handle_notification(self, response, client_callback):
        host, port = response.source
        key = hash(str(host) + str(port) + str(response.token))
        self.relation[key] = (response, time.time(), client_callback)
        if response.type == defines.inv_types["CON"]:
            ack = Message.new_ack(response)
            self.send(ack)

    def cancel_observing(self, response, send_rst):
        host, port = response.source
        key = hash(str(host) + str(port) + str(response.token))
        del self.relation[key]
        if send_rst:
            rst = Message.new_rst(response)
            self.send(rst)

    def post(self, client_callback, *args, **kwargs):
        if isinstance(args[0], tuple):
            path, payload = args
            req = Request()
            req.uri_path = path
            if "Token" in kwargs.keys():
                req.token = kwargs.get("Token")
                del kwargs["Token"]
            if "MID" in kwargs.keys():
                req.mid = kwargs.get("MID")
                del kwargs["MID"]
            if "Server" in kwargs.keys():
                req.destination = kwargs.get("Server")
                del kwargs["Server"]
        else:
            req = args[0]
        for key in kwargs:
            try:
                o = Option()
                o.number = defines.inv_options[key]
                o.value = kwargs[key]
                req.add_option(o)
            except KeyError:
                pass
        req.code = defines.inv_codes['POST']
        req.type = defines.inv_types["CON"]
        self.send_callback(req, self.post_results, client_callback)

    def post_results(self, mid, client_callback):
        key = hash(str(self.server[0]) + str(self.server[1]) + str(mid))
        response = self.received.get(key)
        if key in self.call_id.keys():
            handler, retransmit_count = self.call_id.get(key)
            if handler is not None:
                try:
                    log.msg("Cancel retrasmission")
                    handler.cancel()
                except AlreadyCancelled:
                    pass
        err_callback = None
        if isinstance(client_callback, tuple) and len(client_callback) > 1:
            client_callback, err_callback = client_callback
        elif isinstance(client_callback, tuple):
            client_callback = client_callback[0]
        if response is not None:
            # self.parse_core_link_format(response.payload)
            client_callback(response)
        elif err_callback is not None:
            err_callback(mid, self.server[0], self.server[1])

    def put(self, client_callback, *args, **kwargs):
        if isinstance(args[0], tuple):
            path, payload = args
            req = Request()
            req.uri_path = path
            if "Token" in kwargs.keys():
                req.token = kwargs.get("Token")
                del kwargs["Token"]
            if "MID" in kwargs.keys():
                req.mid = kwargs.get("MID")
                del kwargs["MID"]
            if "Server" in kwargs.keys():
                req.destination = kwargs.get("Server")
                del kwargs["Server"]
        else:
            req = args[0]
        for key in kwargs:
            try:
                o = Option()
                o.number = defines.inv_options[key]
                o.value = kwargs[key]
                req.add_option(o)
            except KeyError:
                pass
        req.code = defines.inv_codes['PUT']
        req.type = defines.inv_types["CON"]
        self.send_callback(req, self.put_results, client_callback)

    def put_results(self, mid, client_callback):
        key = hash(str(self.server[0]) + str(self.server[1]) + str(mid))
        response = self.received.get(key)
        if key in self.call_id.keys():
            handler, retransmit_count = self.call_id.get(key)
            if handler is not None:
                try:
                    log.msg("Cancel retrasmission")
                    handler.cancel()
                except AlreadyCancelled:
                    pass
        err_callback = None
        if isinstance(client_callback, tuple) and len(client_callback) > 1:
            client_callback, err_callback = client_callback
        elif isinstance(client_callback, tuple):
            client_callback = client_callback[0]
        if response is not None:
            # self.parse_core_link_format(response.payload)
            client_callback(response)
        elif err_callback is not None:
            err_callback(mid, self.server[0], self.server[1])

    def delete(self, client_callback, *args, **kwargs):
        if isinstance(args[0], str):
            path = str(args[0])
            req = Request()
            req.uri_path = path
            if "Token" in kwargs.keys():
                req.token = kwargs.get("Token")
                del kwargs["Token"]
            if "MID" in kwargs.keys():
                req.mid = kwargs.get("MID")
                del kwargs["MID"]
            if "Server" in kwargs.keys():
                req.destination = kwargs.get("Server")
                del kwargs["Server"]
        else:
            req = args[0]
        for key in kwargs:
            try:
                o = Option()
                o.number = defines.inv_options[key]
                o.value = kwargs[key]
                req.add_option(o)
            except KeyError:
                pass
        req.code = defines.inv_codes['DELETE']
        req.type = defines.inv_types["CON"]
        self.send_callback(req, self.delete_results, client_callback)

    def delete_results(self, mid, client_callback):
        key = hash(str(self.server[0]) + str(self.server[1]) + str(mid))
        response = self.received.get(key)
        if key in self.call_id.keys():
            handler, retransmit_count = self.call_id.get(key)
            if handler is not None:
                try:
                    log.msg("Cancel retrasmission")
                    handler.cancel()
                except AlreadyCancelled:
                    pass
        err_callback = None
        if isinstance(client_callback, tuple) and len(client_callback) > 1:
            client_callback, err_callback = client_callback
        elif isinstance(client_callback, tuple):
            client_callback = client_callback[0]
        if response is not None:
            # self.parse_core_link_format(response.payload)
            client_callback(response)
        elif err_callback is not None:
            err_callback(mid, self.server[0], self.server[1])

    def schedule_retrasmission(self, request, err_callback):
        host, port = self.server
        if request.type == defines.inv_types['CON']:
            future_time = random.uniform(defines.ACK_TIMEOUT, (defines.ACK_TIMEOUT * defines.ACK_RANDOM_FACTOR))
            key = hash(str(host) + str(port) + str(request.mid))
            self.call_id[key] = (reactor.callLater(future_time, self.retransmit,
                                                   (request, host, port, future_time, err_callback)), 0)

    def retransmit(self, t):
        log.msg("Retransmit")
        request, host, port, future_time, err_callback = t
        key = hash(str(host) + str(port) + str(request.mid))
        call_id, retransmit_count = self.call_id[key]
        if retransmit_count < defines.MAX_RETRANSMIT and (not request.acknowledged and not request.rejected):
            retransmit_count += 1
            req, timestamp, callback, client_callback = self.sent[key]
            self.sent[key] = (request, time.time(), callback, client_callback)
            self.send(request)
            future_time *= 2
            self.call_id[key] = (reactor.callLater(future_time, self.retransmit,
                                                   (request, host, port, future_time, err_callback)), retransmit_count)

        elif request.acknowledged or request.rejected:
            request.timeouted = False
            del self.call_id[key]
        else:
            request.timeouted = True
            log.err("Request timeouted")
            del self.call_id[key]
            if err_callback is not None:
                err_callback(request.mid, host, port)


class HelperClient(object):
    def __init__(self, server=("bbbb::2", 5683), forward=False):
        # print "INIT HELPER\n"
        self.protocol = CoAP(server, forward)
        reactor.listenUDP(0, self.protocol)
        #reactor.run()

    @property
    def starting_mid(self):
        return self.protocol.current_mid

    @starting_mid.setter
    def starting_mid(self, mid):
        self.protocol.current_mid = mid

    def start(self, operations):
        # print "START HELPER\n"
        self.protocol.set_operations(operations)