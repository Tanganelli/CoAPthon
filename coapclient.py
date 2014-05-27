import random
import re
import time
from twisted.python import log
from coapthon2 import defines
from coapthon2.messages.request import Request
from coapthon2.messages.response import Response
from coapthon2.resources.resource import Resource
from coapthon2.serializer import Serializer
from twisted.internet import task
from coapthon2.utils import Tree

__author__ = 'giacomo'

from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor


class EchoClientDatagramProtocol(DatagramProtocol):
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

    def startProtocol(self):
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
            del self.sent[key]
            del self.sent_token[key_token]
            del self.received[key]
            del self.received_token[key_token]

    def start(self, host):
        self.server = (host, self.server[1])
        self.transport.connect(host, self.server[1])
        self.discover()

    def send(self, req):
        self._currentMID += 1
        req.mid = self._currentMID
        key = hash(str(self.server[0]) + str(self.server[1]) + str(req.mid))
        key_token = hash(str(self.server[0]) + str(self.server[1]) + str(req.token))
        self.sent[key] = (req, time.time(), self.discover_results)
        self.sent_token[key_token] = (req, time.time(), self.discover_results)
        self.schedule_retrasmission(req)
        serializer = Serializer()
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

    def discover(self):
        req = Request()
        req.code = defines.inv_codes['GET']
        req.uri_path = ".well-known/core"
        req.type = defines.inv_types["CON"]
        self.send(req)

    def discover_results(self, mid):
        key = hash(str(self.server[0]) + str(self.server[1]) + str(mid))
        response = self.received.get(key)
        if key in self.call_id.keys():
            handler, retransmit_count = self.call_id.get(key)
            if handler is not None:
                log.msg("Cancel retrasmission")
                handler.cancel()
        if response is not None:
            self.parse_core_link_format(response.payload)

    def parse_core_link_format(self, link_format):
        while len(link_format) > 0:
            pattern = "<([^>]*)>;"
            result = re.match(pattern, link_format)
            path = result.group(1)
            path = path.split("/")
            path = path[1:]
            link_format = link_format[result.end(1) + 2:]
            pattern = "([^,])*"
            result = re.match(pattern, link_format)
            attributes = result.group(0)
            attributes = attributes.split(";")
            dict_att = {}
            for att in attributes:
                a = att.split("=")
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

    def schedule_retrasmission(self, request):
        host, port = self.server
        if request.type == defines.inv_types['CON']:
            future_time = random.uniform(defines.ACK_TIMEOUT, (defines.ACK_TIMEOUT * defines.ACK_RANDOM_FACTOR))
            key = hash(str(host) + str(port) + str(request.mid))
            self.call_id[key] = (reactor.callLater(future_time, self.retransmit,
                                                   (request, host, port, future_time)), 0)

    def retransmit(self, t):
        request, host, port, future_time = t
        key = hash(str(host) + str(port) + str(request.mid))
        call_id, retransmit_count = self.call_id[key]
        if retransmit_count < defines.MAX_RETRANSMIT and (not request.acknowledged and not request.rejected):
            retransmit_count += 1
            self.sent[key] = (request, time.time())
            serializer = Serializer()
            datagram = serializer.serialize(request)
            self.transport.write(datagram, (host, port))
            future_time *= 2
            self.call_id[key] = (reactor.callLater(reactor, future_time, self.retransmit,
                                                   (request, host, port, future_time)), retransmit_count)

        elif request.acknowledged or request.rejected:
            request.timeouted = False
            del self.call_id[key]
        else:
            request.timeouted = True
            del self.call_id[key]


def main():
    protocol = EchoClientDatagramProtocol()
    t = reactor.listenUDP(0, protocol)
    reactor.run()

if __name__ == '__main__':
    main()