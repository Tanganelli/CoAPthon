import random
import sys
import time
from twisted.python import log
from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor, threads, task
from coapthon2 import defines
from coapthon2.layer.message import MessageLayer
from coapthon2.layer.observe import ObserveLayer
from coapthon2.layer.request import RequestLayer
from coapthon2.layer.resource import ResourceLayer
from coapthon2.messages.message import Message
from coapthon2.messages.request import Request
from coapthon2.messages.response import Response
from coapthon2.resources.hello import Hello
from coapthon2.resources.resource import Resource
from coapthon2.serializer import Serializer
from coapthon2.utils import Tree

__author__ = 'Giacomo Tanganelli'
__version__ = "2.0"
log.startLogging(sys.stdout)


class CoAP(DatagramProtocol):
    def __init__(self):
        self.received = {}
        self.sent = {}
        self.call_id = {}
        self.relation = {}
        self._currentMID = 1

        root = Resource('root', visible=False, observable=False, allow_children=True)
        root.path = '/'
        self.root = Tree(root)

        l = task.LoopingCall(self.purge_mids)
        l.start(defines.EXCHANGE_LIFETIME)

        self._request_layer = RequestLayer(self)
        self._resource_layer = ResourceLayer(self)
        self._message_layer = MessageLayer(self)
        self._observe_layer = ObserveLayer(self)

    def datagramReceived(self, data, (host, port)):
        log.msg("Datagram received from " + str(host) + ":" + str(port))
        serializer = Serializer()
        message = serializer.serialize_request(data, host, port)
        if isinstance(message, Request):
            log.msg("Received request")
            ret = self._request_layer.handle_request(message)
            if isinstance(ret, Request):
                response = self._request_layer.process(ret)
            else:
                response = ret
            self.schedule_retrasmission((response, host, port))
            response = serializer.serialize_response(response)
            self.transport.write(response, (host, port))
        elif isinstance(message, Response):
            log.err("Received response")
            rst = Message.new_rst(message)
            rst = self._message_layer.matcher_response(rst)
            response = serializer.serialize_response(rst)
            self.transport.write(response, (host, port))
        else:
            # ACK or RST
            log.msg("Received ACK or RST")
            self._message_layer.handle_message(message)

    def purge_mids(self):
        now = time.time()
        sent_key_to_delete = []
        for key in self.sent:
            message, timestamp = self.sent.get(key)
            if timestamp + defines.EXCHANGE_LIFETIME <= now:
                sent_key_to_delete.append(key)
        received_key_to_delete = []
        for key in self.received:
            message, timestamp = self.received.get(key)
            if timestamp + defines.EXCHANGE_LIFETIME <= now:
                received_key_to_delete.append(key)
        for key in sent_key_to_delete:
            del self.sent[key]
        for key in received_key_to_delete:
            del self.received[key]

    def add_resource(self, path, resource):
        assert isinstance(resource, Resource)
        path = path.strip("/")
        paths = path.split("/")
        old = self.root
        i = 0
        for p in paths:
            i += 1
            res = old.find(p)
            if res is None:
                if len(paths) != i:
                    return False
                resource.path = p
                resource.content_type = "text/plain"
                resource.resource_type = "prova"
                resource.maximum_size_estimated = 10
                old = old.add_child(resource)
            else:
                old = res
        return True

    @property
    def current_mid(self):
        return self._currentMID

    @current_mid.setter
    def current_mid(self, mid):
        self._currentMID = int(mid)

    def add_observing(self, resource, response):
        return self._observe_layer.add_observing(resource, response)

    def reliability_response(self, request, response):
        return self._message_layer.reliability_response(request, response)

    def matcher_response(self, response):
        return self._message_layer.matcher_response(response)

    def create_resource(self, path, request, response):
        return self._resource_layer.create_resource(path, request, response)

    def update_resource(self, path, request, response, resource, render_method="render_PUT"):
        return self._resource_layer.update_resource(path, request, response, resource, render_method)

    def delete_resource(self, request, response, node):
        return self._resource_layer.delete_resource(request, response, node)

    def get_resource(self, request, response, resource):
        return self._resource_layer.get_resource(request, response, resource)

    def discover(self, request, response):
        return self._resource_layer.discover(request, response)

    def notify(self, node):
        commands = self._observe_layer.notify(node)
        if commands is not None:
            threads.callMultipleInThread(commands)

    def remove_observers(self, node):
        commands = self._observe_layer.remove_observers(node)
        if commands is not None:
            threads.callMultipleInThread(commands)

    def prepare_notification(self, t):
        ret = self._observe_layer.prepare_notification(t)
        if ret is not None:
            reactor.callFromThread(self._observe_layer.send_notification, ret)

    def schedule_retrasmission(self, t):
        response, host, port = t
        if response.type == defines.inv_types['CON']:
            future_time = random.uniform(defines.ACK_TIMEOUT, (defines.ACK_TIMEOUT * defines.ACK_RANDOM_FACTOR))
            key = hash(str(host) + str(port) + str(response.mid))
            self.call_id[key] = (reactor.callLater(future_time, self.retransmit,
                                                   (response, host, port, future_time)), 0)

    def retransmit(self, t):
        response, host, port, future_time = t
        key = hash(str(host) + str(port) + str(response.mid))
        call_id, retransmit_count = self.call_id[key]
        if retransmit_count < defines.MAX_RETRANSMIT and (not response.acknowledged and not response.rejected):
            retransmit_count += 1
            self.sent[key] = (response, time.time())
            self.transport.write(response, (host, port))
            future_time *= 2
            self.call_id[key] = (reactor.callLater(reactor, future_time, self.retransmit,
                                                   (response, host, port, future_time)), retransmit_count)

        elif response.acknowledged or response.rejected:
            response.timeouted = False
            del self.call_id[key]
        else:
            response.timeouted = True
            del self.call_id[key]

    @staticmethod
    def send_error(request, response, error):
        response.type = defines.inv_types['NON']
        response.code = defines.responses[error]
        response.token = request.token
        response.mid = request.mid
        return response


class CoAPServer(CoAP):
    def __init__(self):
        CoAP.__init__(self)
        if self.add_resource('hello/', Hello('hello')):
            log.msg(self.root.dump())
        if self.add_resource('hello/hello2', Hello('hello')):
            log.msg(self.root.dump())


reactor.listenUDP(5683, CoAPServer())
reactor.run()
