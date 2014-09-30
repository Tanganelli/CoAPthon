import random
import re
import time
import twisted
from twisted.application.service import Application
from twisted.internet.error import AlreadyCancelled
from twisted.python import log
from twisted.python.log import ILogObserver, FileLogObserver
from twisted.python.logfile import DailyLogFile
from coapthon2 import defines
from coapthon2.messages.message import Message
from coapthon2.messages.option import Option
from coapthon2.messages.request import Request
from coapthon2.messages.response import Response
from coapthon2.resources.resource import Resource
from coapthon2.serializer import Serializer
from twisted.internet import task
from coapthon2.utils import Tree
from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor

__author__ = 'Giacomo Tanganelli'
__version__ = "2.0"

from os.path import expanduser
home = expanduser("~")

# First, startLogging to capture stdout
logfile = DailyLogFile("CoAPthon_client.log", home + "/.coapthon/")
# Now add an observer that logs to a file
application = Application("CoAPthon_Client")
application.setComponent(ILogObserver, FileLogObserver(logfile).emit)


class CoAP(DatagramProtocol):
    def __init__(self, server, forward):
        self._forward = forward
        self.received = {}
        self.sent = {}
        self.sent_token = {}
        self.received_token = {}
        self.call_id = {}
        self.relation = {}
        self._currentMID = 1
        #defer = reactor.resolve('coap.me')
        #defer.addCallback(self.start)
        #self.server = (None, 5683)
        self.server = server
        root = Resource('root', visible=False, observable=False, allow_children=True)
        root.path = '/'
        self.root = Tree(root)
        self.operations = []
        self.l = None
        self.transport = None

    def set_operations(self, operations):
        for op in operations:
            function, args, kwargs, client_callback = op
            self.operations.append((function, args, kwargs, client_callback))

    def startProtocol(self):
        if self.server is None:
            log.err("Server address for the client is not initialized")
            exit()
        host, port = self.server
        if host is not None:
            self.start(host)
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
        #self.server = (host, self.server[1])
        self.transport.connect(host, self.server[1])
        function, args, kwargs, client_callback = self.get_operation()
        function(client_callback, *args, **kwargs)

    def start_test(self, transport):
        self.transport = transport
        function, args, kwargs, client_callback = self.get_operation()
        function(client_callback, *args, **kwargs)

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
        serializer = Serializer()
        message.destination = self.server
        host, port = message.destination
        print "Message sent to " + host + ":" + str(port)
        print "----------------------------------------"
        print message
        print "----------------------------------------"
        datagram = serializer.serialize(message)
        log.msg("Send datagram")
        self.transport.write(datagram)

    def send_callback(self, req, callback, client_callback):
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
        serializer = Serializer()
        host, port = host
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
            #Separate Response
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
        key = hash(str(self.server[0]) + str(self.server[1]) + str(message.mid))
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
            #self.parse_core_link_format(response.payload)
            client_callback(response)
        elif err_callback is not None:
            err_callback(mid, self.server[0], self.server[1])

    def parse_core_link_format(self, link_format):
        while len(link_format) > 0:
            pattern = "<([^>]*)>;"
            result = re.match(pattern, link_format)
            path = result.group(1)
            path = path.split("/")
            path = path[1:]
            link_format = link_format[result.end(1) + 2:]
            pattern = "([^<,])*"
            result = re.match(pattern, link_format)
            attributes = result.group(0)
            dict_att = {}
            if len(attributes) > 0:
                attributes = attributes.split(";")
                for att in attributes:
                    a = att.split("=")
                    # TODO check correctness
                    dict_att[a[0]] = a[1]
                link_format = link_format[result.end(0) + 1:]

            while True:
                last, p = self.root.find_complete_last(path)
                if p is not None:
                    resource = Resource("/".join(path))
                    resource.path = p
                    if p == "".join(path):
                        resource.attributes = dict_att
                    last.add_child(resource)
                else:
                    break
        log.msg(self.root.dump())

    def get(self, client_callback, *args, **kwargs):
        path = args[0]
        req = Request()
        if "Token" in kwargs.keys():
            req.token = kwargs.get("Token")
            del kwargs["Token"]
        for key in kwargs:
            o = Option()
            o.number = defines.inv_options[key]
            o.value = kwargs[key]
            req.add_option(o)

        req.code = defines.inv_codes['GET']
        req.uri_path = path
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
            #self.parse_core_link_format(response.payload)
            client_callback(response)
        elif err_callback is not None:
            err_callback(mid, self.server[0], self.server[1])

    def observe(self, client_callback, *args, **kwargs):
        path = args[0]
        req = Request()
        if "Token" in kwargs.keys():
            req.token = kwargs.get("Token")
            del kwargs["Token"]
        for key in kwargs:
            o = Option()
            o.number = defines.inv_options[key]
            o.value = kwargs[key]
            req.add_option(o)

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
                #TODO add observing results
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
        path, payload = args
        req = Request()
        if "Token" in kwargs.keys():
            req.token = kwargs.get("Token")
            del kwargs["Token"]
        for key in kwargs:
            o = Option()
            o.number = defines.inv_options[key]
            o.value = kwargs[key]
            req.add_option(o)
        req.code = defines.inv_codes['POST']
        req.uri_path = path
        req.type = defines.inv_types["CON"]
        req.payload = payload
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
            #self.parse_core_link_format(response.payload)
            client_callback(response)
        elif err_callback is not None:
            err_callback(mid, self.server[0], self.server[1])

    def put(self, client_callback, *args, **kwargs):
        path, payload = args
        req = Request()
        if "Token" in kwargs.keys():
            req.token = kwargs.get("Token")
            del kwargs["Token"]
        for key in kwargs:
            o = Option()
            o.number = defines.inv_options[key]
            o.value = kwargs[key]
            req.add_option(o)
        req.code = defines.inv_codes['PUT']
        req.uri_path = path
        req.type = defines.inv_types["CON"]
        req.payload = payload
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
            #self.parse_core_link_format(response.payload)
            client_callback(response)
        elif err_callback is not None:
            err_callback(mid, self.server[0], self.server[1])

    def delete(self, client_callback, *args, **kwargs):
        path = args[0]
        req = Request()
        if "Token" in kwargs.keys():
            req.token = kwargs.get("Token")
            del kwargs["Token"]
        for key in kwargs:
            o = Option()
            o.number = defines.inv_options[key]
            o.value = kwargs[key]
            req.add_option(o)
        req.code = defines.inv_codes['DELETE']
        req.uri_path = path
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
            #self.parse_core_link_format(response.payload)
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
    def __init__(self, server=("127.0.0.1", 5683), forward=False):
        self.protocol = CoAP(server, forward)

    @property
    def starting_mid(self):
        return self.protocol._currentMID

    @starting_mid.setter
    def starting_mid(self, mid):
        self.protocol._currentMID = mid

    def start(self, operations):
        self.protocol.set_operations(operations)
        reactor.listenUDP(0, self.protocol)
        try:
            reactor.run()
        except twisted.internet.error.ReactorAlreadyRunning:
            log.msg("Reactor already started")


