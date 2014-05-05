import sys
import time
from twisted.python import log
from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor
from coapthon2 import defines
from coapthon2.messages.message import Message
from coapthon2.messages.option import Option
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
        self._mid_received = {}
        self._token_received = {}
        self._mid_sent = {}
        self._token_sent = {}

        root = Resource('root', visible=False, observable=False, allow_children=True)
        root.path = '/'
        self.root = Tree(root)
        self._relation = {}
        self._currentMID = 1

    def datagramReceived(self, data, (host, port)):
        log.msg("Datagram received from " + str(host) + ":" + str(port))
        serializer = Serializer()
        message = serializer.serialize_request(data, host, port)
        if isinstance(message, Request):
            ret = self.handle_request(message)
            if isinstance(ret, Request):
                response = self.process(ret)
            else:
                response = ret
            response = serializer.serialize_response(response)
            self.transport.write(response, (host, port))

    def handle_request(self, request):
        if request.mid not in self._mid_received:
            self._token_received[request.token] = self._mid_received[request.mid] = request
            self._token_sent[request.token] = self._mid_sent[request.mid] = None
            # TODO Blockwise
            return request
        else:
            request.duplicated = True
            response = self._mid_sent[request.mid]
            if isinstance(response, response):
                return response
            elif request.acknowledged:
                ack = Message.new_ack(request)
                return ack
            elif request.rejected:
                rst = Message.new_rst(request)
                return rst
            else:
                # The server has not yet decided, whether to acknowledge or
                # reject the request. We know for sure that the server has
                # received the request though and can drop this duplicate here.
                return None

    def process(self, request):
        method = defines.codes[request.code]
        if method == 'GET':
            response = self.handle_get(request)
        elif method == 'POST':
            response = self.handle_post(request)
        elif method == 'PUT':
            response = self.handle_put(request)
        elif method == 'DELETE':
            response = self.handle_delete(request)
        else:
            response = None
        return response

    def handle_put(self, request):
        path = request.uri_path
        path = path.strip("/")
        node = self.root.find_complete(path)
        if node is not None:
            resource = node.value
        else:
            resource = None
        response = Response()
        response.destination = request.source
        if resource is None:
            # Create request
            response = self.create_resource(path, resource, request, response)
            return response

    def handle_get(self, request):
        path = request.uri_path
        path = path.strip("/")
        node = self.root.find_complete(path)
        if node is not None:
            resource = node.value
        else:
            resource = None
        response = Response()
        response.destination = request.source
        if resource is None:
            response = self.send_error(request, response, 'NOT_FOUND')
        else:
            method = getattr(resource, 'render_GET', None)
            if hasattr(method, '__call__'):
                #TODO handle ETAG
                # Render_GET
                response.code = defines.responses['CONTENT']
                response.payload = method()
                # Token
                response.token = request.token
                # Observe
                if request.observe and resource.observable:
                    response, resource = self.add_observing(resource, response)
                #TODO Blockwise
                #Reliability
                response = self.reliability_response(request, response)
                #Matcher
                response = self.matcher_response(response)
            else:
                response = self.send_error(request, response, 'METHOD_NOT_ALLOWED')
        return response

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
                if old.value.allow_children:
                    resource.path = p
                    old = old.add_child(resource)
                else:
                    return False
            else:
                old = res
        return True

    def add_observing(self, resource, response):
        host, port = response.source
        log.msg("Initiate an observe relation between " + str(host) + ":" +
                str(port) + " and resource " + str(resource.path))
        key = hash(str(host) + str(port) + str(resource.path))
        observers = self._relation.get(resource)
        now = int(round(time.time() * 1000))
        observe_count = resource.observe_count
        if observers is None:
            observers = {key: now}
        else:
            subscriber = observers.get(key)
            if subscriber is None:
                observers[key] = now
            else:
                observe_count, last = observers[key]
                observers[key] = now
        self._relation[resource] = observers
        option = Option()
        option.number = defines.inv_options['Observe']
        option.value = observe_count
        response.add_option(option)
        resource.observe_count += 1
        return response, resource

    def reliability_response(self, request, response):
        if not (response.type == defines.inv_types['ACK'] or response.type == defines.inv_types['RST']):
            if request.type == defines.inv_types['CON']:
                if request.acknowledged:
                    response.type = defines.inv_types['CON']
                else:
                    request.acknowledged = True
                    response.type = defines.inv_types['ACK']
                    response.mid = request.mid
            else:
                response.type = defines.inv_types['NON']
        else:
            response.mid = request.mid

        if response.type == defines.inv_types['CON']:
            #TODO set retransmission handler
            pass
        return response

    def matcher_response(self, response):
        if response.mid is None:
            response.mid = self._currentMID % (1 << 16)
            self._currentMID += 1
        host, port = response.destination
        if host is None:
            raise AttributeError("Response has no destination address set")
        if port is None or port == 0:
            raise AttributeError("Response hsa no destination port set")
        self._mid_sent[response.mid] = self._token_sent[response.token] = response
        return response

    @staticmethod
    def send_error(request, response, error):
        response.type = defines.inv_types['NON']
        response.code = defines.responses[error]
        response.token = request.token
        response.mid = request.mid
        return response

    def create_resource(self, path, resource, request, response):
        paths = path.split("/")
        old = self.root
        for p in paths:
            res = old.find(p)
            if res is None:
                if old.value.allow_children:
                    method = getattr(resource, 'render_PUT', None)
                    if hasattr(method, '__call__'):
                        resource = method()
                        if resource is not None:
                            resource.path = p
                            old = old.add_child(resource)
                            response.code = defines.responses['CREATED']
                            response.payload = None
                            # Token
                            response.token = request.token
                            # Observe
                            self.notify(old.parent)
                            #TODO Blockwise
                            #Reliability
                            response = self.reliability_response(request, response)
                            #Matcher
                            response = self.matcher_response(response)
                            return response
                        else:
                            return self.send_error(request, response, 'INTERNAL_SERVER_ERROR')
                    else:
                        return self.send_error(request, response, 'METHOD_NOT_ALLOWED')
                else:
                    return self.send_error(request, response, 'METHOD_NOT_ALLOWED')
            else:
                old = res

    def notify(self, node):
        pass


class CoAPServer(CoAP):
    def __init__(self):
        CoAP.__init__(self)
        if self.add_resource('hello/', Hello('hello')):
            log.msg(self.root.dump())
        if self.add_resource('hello/hello2', Hello('hello')):
            log.msg(self.root.dump())


reactor.listenUDP(5683, CoAPServer())
reactor.run()
