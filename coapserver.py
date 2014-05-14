import random
import sys
import time
from twisted.python import log
from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor, threads
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
        self._callID = {}

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
            if response.type == defines.inv_types['CON']:
                future_time = random.uniform(defines.ACK_TIMEOUT, (defines.ACK_TIMEOUT * defines.ACK_RANDOM_FACTOR))
                key = hash(str(host) + str(port) + str(response.mid))
                self._callID[key] = (reactor.callLater(reactor, future_time, self.retransmit, (response, host, port,
                                                                                               future_time)), 0)

            self.transport.write(response, (host, port))
        elif isinstance(message, Response):
            log.err("Received response")
            rst = Message.new_rst(message)
            response = serializer.serialize_response(rst)
            self.transport.write(response, (host, port))
        else:
            # ACK or RST
            self.handle_message(message)

    def retransmit(self, t):
        response, host, port, future_time = t
        key = hash(str(host) + str(port) + str(response.mid))
        call_id, retransmit_count = self._callID[key]
        if retransmit_count < defines.MAX_RETRANSMIT and (not response.acknowledged and not response.rejected):
            retransmit_count += 1
            self.transport.write(response, (host, port))
            future_time *= 2
            self._callID[key] = (reactor.callLater(reactor, future_time, self.retransmit, (response, host, port,
                                                                                           future_time)),
                                 retransmit_count)
        else:
            response.timeouted = True
            del self._callID[key]

    def handle_message(self, message):
        # Matcher
        if message.mid not in self._mid_sent:
            log.err(defines.types[message.type] + " received without the corresponding message")
            return
            # Reliability
        response = self._mid_sent[message.mid]
        if message.type == defines.inv_types['ACK']:
            response.acknowledged = True
        elif message.type == defines.inv_types['RST']:
            response.rejected = True
            # TODO Blockwise
        # Observing
        if message.type == defines.inv_types['RST']:
            for resource in self._relation.keys():
                host, port = message.source
                key = hash(str(host) + str(port) + str(response.token))
                observers = self._relation[resource]
                del observers[key]
                log.msg("Cancel observing relation")
                if len(observers) == 0:
                    del self._relation[resource]

        # cancel retransmission
        host, port = message.source
        key = hash(str(host) + str(port) + str(message.mid))
        call_id, retrasmission_count = self._callID.get(key, None)
        if call_id is not None:
            call_id.cancel()
        return

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
            response = self.create_resource(path, request, response)
            log.msg("Resource created")
            log.msg(self.root.dump())
            return response
        else:
            # Update request
            response = self.update_resource(path, request, response, resource)
            log.msg("Resource updated")
            return response

    def handle_post(self, request):
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
            response = self.create_resource(path, request, response)
            log.msg("Resource created")
            log.msg(self.root.dump())
            return response
        else:
            # Update request
            response = self.update_resource(path, request, response, resource)
            log.msg("Resource updated")
            return response

    def handle_delete(self, request):
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
            response = self.send_error(request, response, 'NOT_FOUND')
            log.msg("Resource Not Found")
            return response
        else:
            # Delete
            response = self.delete_resource(request, response, node)
            log.msg("Resource deleted")
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
            # Not Found
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
                resource.path = p
                old = old.add_child(resource)
            else:
                old = res
        return True

    def add_observing(self, resource, response):
        host, port = response.destination
        key = hash(str(host) + str(port) + str(response.token))
        observers = self._relation.get(resource)
        now = int(round(time.time() * 1000))
        observe_count = resource.observe_count
        if observers is None:
            log.msg("Initiate an observe relation between " + str(host) + ":" +
                    str(port) + " and resource " + str(resource.path))
            observers = {key: (now, host, port, response.token)}
        elif key not in observers:
            log.msg("Initiate an observe relation between " + str(host) + ":" +
                    str(port) + " and resource " + str(resource.path))
            observers[key] = (now, host, port, response.token)
        else:
            log.msg("Update observe relation between " + str(host) + ":" +
                    str(port) + " and resource " + str(resource.path))
            old, host, port, token = observers[key]
            observers[key] = (now, host, port, token)
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

    def create_resource(self, path, request, response):
        paths = path.split("/")
        old = self.root
        for p in paths:
            res = old.find(p)
            if res is None:
                if old.value.allow_children:
                    method = getattr(old.value, 'render_PUT', None)
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

    def update_resource(self, path, request, response, resource):
        path = path.strip("/")
        node = self.root.find_complete(path)
        method = getattr(resource, 'render_PUT', None)
        if hasattr(method, '__call__'):
            new_resource = method(False, request.payload)
            if new_resource is not None:
                node.value = new_resource
                response.code = defines.responses['CHANGED']
                response.payload = None
                # Token
                response.token = request.token
                # Observe
                self.notify(node)
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

    def delete_resource(self, request, response, node):
        assert isinstance(node, Tree)
        method = getattr(node.value, 'render_DELETE', None)
        if hasattr(method, '__call__'):
            ret = method()
            if ret:
                parent = node.parent
                assert isinstance(parent, Tree)
                parent.del_child(node)
                response.code = defines.responses['DELETED']
                response.payload = None
                # Token
                response.token = request.token
                # Observe
                self.notify(parent)
                self.remove_observes(node)
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

    def notify(self, node):
        assert isinstance(node, Tree)
        resource = node.value
        observers = self._relation.get(resource)
        if observers is None:
            return
        now = int(round(time.time() * 1000))
        commands = []
        for item in observers.keys():
            old, host, port, token = observers[item]
            #send notification
            commands.append((self.prepare_notification, [(resource, host, port, token)], {}))
            observers[item] = (now, host, port, token)
        resource.observe_count += 1
        self._relation[resource] = observers
        threads.callMultipleInThread(commands)

    def prepare_notification(self, t):
        resource, host, port, token = t
        response = Response()
        response.destination = (host, port)
        response.token = token
        option = Option()
        option.number = defines.inv_options['Observe']
        option.value = resource.observe_count
        response.add_option(option)
        method = getattr(resource, 'render_GET', None)
        if hasattr(method, '__call__'):
            # Render_GET
            response.code = defines.responses['CONTENT']
            response.payload = method()
            #TODO Blockwise
            #Reliability
            request = Request()
            request.type = defines.inv_types['NON']
            response = self.reliability_response(request, response)
            #Matcher
            response = self.matcher_response(response)
            reactor.callFromThread(self.send_notification, (response, host, port))

    def send_notification(self, t):
        response, host, port = t
        serializer = Serializer()
        response = serializer.serialize_response(response)
        self.transport.write(response, (host, port))

    def remove_observers(self, node):
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
