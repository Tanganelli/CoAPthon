import random
import re
import time
from twisted.internet.error import AlreadyCancelled
from twisted.python import log
from coapthon2 import defines
from coapthon2.messages.message import Message
from coapthon2.messages.option import Option
from coapthon2.messages.request import Request
from coapthon2.messages.response import Response
from coapthon2.resources.resource import Resource
from coapthon2.serializer import Serializer
from twisted.internet import task
from coapthon2.utils import Tree

__author__ = 'giacomo'

from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor


class CoAP(DatagramProtocol):
    def __init__(self):
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
        self.server = ("127.0.0.1", 5683)
        root = Resource('root', visible=False, observable=False, allow_children=True)
        root.path = '/'
        self.root = Tree(root)
        self.operations = []

    def startProtocol(self):
        self.operations.append((self.discover,))
        args = ("/hello",)
        kwargs = {}
        self.operations.append((self.observe, args, kwargs))
        # args = ("/hello", "Test")
        # self.operations.append((self.put, args))
        # self.operations.append((self.post, args))
        # self.operations.append((self.discover,))
        # args = ("/pippo/prova/hello3",)
        # self.operations.append((self.delete, args))
        # self.operations.append((self.discover,))
        # self.operations.append((self.get, args))
        host, port = self.server
        if host is not None:
            self.start(host)

        l = task.LoopingCall(self.purge_mids)
        l.start(defines.EXCHANGE_LIFETIME)

    def purge_mids(self):
        log.msg("Purge mids")
        now = time.time()
        sent_key_to_delete = []
        for key in self.sent.keys():
            message, timestamp, callback = self.sent.get(key)
            if timestamp + defines.EXCHANGE_LIFETIME <= now:
                sent_key_to_delete.append(key)
        for key in sent_key_to_delete:
            message, timestamp, callback = self.sent.get(key)
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
        self.server = (host, self.server[1])
        self.transport.connect(host, self.server[1])
        function, args, kwargs = self.get_operation()
        function(*args, **kwargs)

    def get_operation(self):
        try:
            to_exec = self.operations.pop(0)
            args = []
            kwargs = {}
            if len(to_exec) == 3:
                function, args, kwargs = to_exec
            elif len(to_exec) == 2:
                function, args = to_exec
            else:
                function = to_exec[0]
            return function, args, kwargs
        except IndexError:
            return None, None, None

    def send(self, req, callback):
        self._currentMID += 1
        req.mid = self._currentMID
        key = hash(str(self.server[0]) + str(self.server[1]) + str(req.mid))
        key_token = hash(str(self.server[0]) + str(self.server[1]) + str(req.token))
        self.sent[key] = (req, time.time(), callback)
        self.sent_token[key_token] = (req, time.time(), callback)
        self.schedule_retrasmission(req)
        serializer = Serializer()
        print req
        datagram = serializer.serialize(req)
        log.msg("Send datagram")
        self.transport.write(datagram)

    def datagramReceived(self, datagram, host):
        serializer = Serializer()
        host, port = host
        message = serializer.deserialize(datagram, host, port)
        if isinstance(message, Response):
            self.handle_response(message)
        elif isinstance(message, Request):
            log.err("Received request")
        else:
            self.handle_message(message)

        function, args, kwargs = self.get_operation()
        key = hash(str(host) + str(port) + str(message.token))
        if function is None and len(self.relation) == 0:
            reactor.stop()
        elif key in self.relation:
            self.handle_notification(message)
        else:
            function(*args, **kwargs)

    def handle_message(self, message):
        key = hash(str(self.server[0]) + str(self.server[1]) + str(message.mid))
        if key in self.sent.keys():
            self.received[key] = message
            req, timestamp, callback = self.sent[key]
            callback(message.mid)

    def handle_response(self, response):
        key_token = hash(str(self.server[0]) + str(self.server[1]) + str(response.token))
        if key_token in self.sent_token.keys():
            self.received_token[key_token] = response
            req, timestamp, callback = self.sent_token[key_token]
            key = hash(str(self.server[0]) + str(self.server[1]) + str(req.mid))
            self.received[key] = response
            callback(req.mid)

    def discover(self, *args, **kwargs):
        req = Request()
        req.code = defines.inv_codes['GET']
        req.uri_path = ".well-known/core"
        req.type = defines.inv_types["CON"]
        self.send(req, self.discover_results)

    def discover_results(self, mid):
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
        if response is not None:
            print response
            self.parse_core_link_format(response.payload)

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

    def get(self, *args, **kwargs):
        path = args[0]
        req = Request()
        for key in kwargs:
            o = Option()
            o.number = defines.inv_options[key]
            o.value = kwargs[key]
            req.add_option(o)

        req.code = defines.inv_codes['GET']
        req.uri_path = path
        req.type = defines.inv_types["CON"]
        self.send(req, self.get_results)

    def get_results(self, mid):
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
        if response is not None:
            print response

    def observe(self, *args, **kwargs):
        path = args[0]
        req = Request()
        for key in kwargs:
            o = Option()
            o.number = defines.inv_options[key]
            o.value = kwargs[key]
            req.add_option(o)

        req.code = defines.inv_codes['GET']
        req.uri_path = path
        req.observe = 0
        req.token = "ciao"
        req.type = defines.inv_types["CON"]
        self.send(req, self.observe_results)

    def observe_results(self, mid):
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
        if response is not None:
            if response.observe != 0:
                #TODO add observing results
                host, port = response.source
                key = hash(str(host) + str(port) + str(response.token))
                self.relation[key] = (response, time.time())
            print response

    def handle_notification(self, response):
        host, port = response.source
        key = hash(str(host) + str(port) + str(response.token))
        self.relation[key] = (response, time.time())
        if response.type == defines.inv_types["CON"]:
            ack = Message.new_ack(response)
            serializer = Serializer()
            datagram = serializer.serialize(ack)
            log.msg("Send datagram")
            self.transport.write(datagram)
        print response

    def post(self, *args, **kwargs):
        path, payload = args
        req = Request()
        for key in kwargs:
            o = Option()
            o.number = defines.inv_options[key]
            o.value = kwargs[key]
            req.add_option(o)
        req.code = defines.inv_codes['POST']
        req.uri_path = path
        req.type = defines.inv_types["CON"]
        req.payload = payload
        self.send(req, self.post_results)

    def post_results(self, mid):
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
        if response is not None:
            print response

    def put(self, *args, **kwargs):
        path, payload = args
        req = Request()
        for key in kwargs:
            o = Option()
            o.number = defines.inv_options[key]
            o.value = kwargs[key]
            req.add_option(o)
        req.code = defines.inv_codes['PUT']
        req.uri_path = path
        req.type = defines.inv_types["CON"]
        req.payload = payload
        self.send(req, self.put_results)

    def put_results(self, mid):
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
        if response is not None:
            print response

    def delete(self, *args, **kwargs):
        path = args[0]
        req = Request()
        for key in kwargs:
            o = Option()
            o.number = defines.inv_options[key]
            o.value = kwargs[key]
            req.add_option(o)
        req.code = defines.inv_codes['DELETE']
        req.uri_path = path
        req.type = defines.inv_types["CON"]
        self.send(req, self.delete_results)

    def delete_results(self, mid):
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
        if response is not None:
            print response

    def schedule_retrasmission(self, request):
        host, port = self.server
        if request.type == defines.inv_types['CON']:
            future_time = random.uniform(defines.ACK_TIMEOUT, (defines.ACK_TIMEOUT * defines.ACK_RANDOM_FACTOR))
            key = hash(str(host) + str(port) + str(request.mid))
            self.call_id[key] = (reactor.callLater(future_time, self.retransmit,
                                                   (request, host, port, future_time)), 0)

    def retransmit(self, t):
        log.msg("Retransmit")
        request, host, port, future_time = t
        key = hash(str(host) + str(port) + str(request.mid))
        call_id, retransmit_count = self.call_id[key]
        if retransmit_count < defines.MAX_RETRANSMIT and (not request.acknowledged and not request.rejected):
            retransmit_count += 1
            req, timestamp, callback = self.sent[key]
            self.sent[key] = (request, time.time(), callback)
            serializer = Serializer()
            datagram = serializer.serialize(request)
            self.transport.write(datagram, (host, port))
            future_time *= 2
            self.call_id[key] = (reactor.callLater(future_time, self.retransmit,
                                                   (request, host, port, future_time)), retransmit_count)

        elif request.acknowledged or request.rejected:
            request.timeouted = False
            del self.call_id[key]
        else:
            request.timeouted = True
            log.err("Request timeouted")
            del self.call_id[key]


def main():
    protocol = CoAP()
    t = reactor.listenUDP(0, protocol)
    reactor.run()

if __name__ == '__main__':
    main()