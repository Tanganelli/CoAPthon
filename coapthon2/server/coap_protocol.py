import random
import time
from twisted.application.service import Application
from twisted.python import log
from twisted.internet.protocol import DatagramProtocol
from twisted.internet import reactor, threads, task
from twisted.python.log import ILogObserver, FileLogObserver
from twisted.python.logfile import DailyLogFile
from coapthon2 import defines
from coapthon2.layer.message import MessageLayer
from coapthon2.layer.observe import ObserveLayer
from coapthon2.layer.request import RequestLayer
from coapthon2.layer.resource import ResourceLayer
from coapthon2.messages.message import Message
from coapthon2.messages.request import Request
from coapthon2.messages.response import Response
from coapthon2.resources.resource import Resource
from coapthon2.serializer import Serializer
from coapthon2.utils import Tree

__author__ = 'Giacomo Tanganelli'
__version__ = "2.0"

from os.path import expanduser
home = expanduser("~")

logfile = DailyLogFile("CoAPthon_server.log", home + "/.coapthon/")
# Now add an observer that logs to a file
application = Application("CoAPthon_Server")
application.setComponent(ILogObserver, FileLogObserver(logfile).emit)


class CoAP(DatagramProtocol):
    def __init__(self, multicast = False):
        """
        Initialize the CoAP protocol

        """
        self.received = {}
        self.sent = {}
        self.call_id = {}
        self.relation = {}
        self._currentMID = random.randint(1, 1000)

        ## Create the resource Tree
        root = Resource('root', visible=False, observable=False, allow_children=True)
        root.path = '/'
        self.root = Tree(root)

        ## Initialize layers
        self._request_layer = RequestLayer(self)
        self._resource_layer = ResourceLayer(self)
        self._message_layer = MessageLayer(self)
        self._observe_layer = ObserveLayer(self)

        ## Start a task for purge MIDs
        self.l = task.LoopingCall(self.purge_mids)
        self.l.start(defines.EXCHANGE_LIFETIME)

        self.multicast = multicast

    def startProtocol(self):
        """
        Called after protocol has started listening.
        """
        # Set the TTL>1 so multicast will cross router hops:
        #self.transport.setTTL(5)
        if self.multicast:
            # Join a specific multicast group:
            self.transport.joinGroup(defines.ALL_COAP_NODES)

    def stopProtocol(self):
        """
        Stop the purge MIDs task

        """
        self.l.stop()

    def send(self, message, host, port):
        """
        Send the message

        :param message: the message to send
        :param host: destination host
        :param port: destination port
        """
        print "Message send to " + host + ":" + str(port)
        print "----------------------------------------"
        print message
        print "----------------------------------------"
        serializer = Serializer()
        message = serializer.serialize(message)
        self.transport.write(message, (host, port))

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
                response = self._request_layer.process(ret)
            else:
                response = ret
            self.schedule_retrasmission(response)
            log.msg("Send Response")
            self.send(response, host, port)
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

    def purge_mids(self):
        """
        Delete messages which has been stored for more than EXCHANGE_LIFETIME.
        Executed in a thread.

        """
        log.msg("Purge MIDs")
        now = time.time()
        sent_key_to_delete = []
        for key in self.sent.keys():
            message, timestamp = self.sent.get(key)
            if timestamp + defines.EXCHANGE_LIFETIME <= now:
                sent_key_to_delete.append(key)
        received_key_to_delete = []
        for key in self.received.keys():
            message, timestamp = self.received.get(key)
            if timestamp + defines.EXCHANGE_LIFETIME <= now:
                received_key_to_delete.append(key)
        for key in sent_key_to_delete:
            del self.sent[key]
        for key in received_key_to_delete:
            del self.received[key]

    def add_resource(self, path, resource):
        """
        Helper function to add resources to the resource Tree during server initialization.

        :param path: path of the resource to create
        :param resource: the actual resource to create
        :return: True, if successful
        """
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
        """
        Get the current MID.

        :return: the current MID used by the server.
        """
        return self._currentMID

    @current_mid.setter
    def current_mid(self, mid):
        """
        Set the current MID.

        :param mid: the MID value
        """
        self._currentMID = int(mid)

    def add_observing(self, resource, response):
        """
        Add an observer to a resource and sets the Observe option in the response.

        :param resource: the resource of interest
        :param response: the response
        :return: response
        """
        return self._observe_layer.add_observing(resource, response)

    def update_relations(self, node, resource):
        """
        Update a relation. It is used when a resource change due a POST request, without changing its path.

        :type node: coapthon2.utils.Tree
        :param node: the node which has the deleted resource
        :param resource: the new resource
        """
        self._observe_layer.update_relations(node, resource)

    def reliability_response(self, request, response):
        """
        Sets Message type according to the request

        :param request: the request object
        :param response: the response object
        :return: the response
        """
        return self._message_layer.reliability_response(request, response)

    def matcher_response(self, response):
        """
        Sets MID if not already set. Save the sent message for acknowledge and duplication handling.

        :param response: the response
        :return: the response
        """
        return self._message_layer.matcher_response(response)

    def create_resource(self, path, request, response):
        """
        Render a POST request.

        :param path: the path of the request
        :param request: the request
        :param response: the response
        :return: the response
        """
        return self._resource_layer.create_resource(path, request, response)

    def update_resource(self, path, request, response):
        """
        Render a PUT request.

        :param path: the path
        :param request: the request
        :param response: the response
        :return: the response
        """
        return self._resource_layer.update_resource(path, request, response)

    def delete_resource(self, request, response, node):
        """
        Render a DELETE request.

        :type node: coapthon2.utils.Tree
        :param request: the request
        :param response: the response
        :param node: the node which has the resource
        :return: the response
        """
        return self._resource_layer.delete_resource(request, response, node)

    def get_resource(self, request, response, resource):
        """
        Render a GET request.

        :param request: the request
        :param response: the response
        :param resource: the resource required
        :return: the response
        """
        return self._resource_layer.get_resource(request, response, resource)

    def discover(self, request, response):
        """
        Render a GET request to the .weel-know/core link.

        :param request: the request
        :param response: the response
        :return: the response
        """
        return self._resource_layer.discover(request, response)

    def notify(self, node):
        """
        Finds the observers that must be notified about the update of the observed resource
        and invoke the notification procedure in different threads.

        :type node: coapthon2.utils.Tree
        :param node: the node which has the deleted resource
        """
        commands = self._observe_layer.notify(node)
        if commands is not None:
            threads.callMultipleInThread(commands)

    def notify_deletion(self, node):
        """
        Finds the observers that must be notified about the delete of the observed resource
        and invoke the notification procedure in different threads.

        :type node: coapthon2.utils.Tree
        :param node: the node which has the deleted resource
        """
        commands = self._observe_layer.notify(node)
        if commands is not None:
            threads.callMultipleInThread(commands)

    def remove_observers(self, node):
        """
        Remove all the observers of a resource and and invoke the notification procedure in different threads.

        :type node: coapthon2.utils.Tree
        :param node: the node which has the deleted resource
        """
        commands = self._observe_layer.remove_observers(node)
        if commands is not None:
            threads.callMultipleInThread(commands)

    def prepare_notification(self, t):
        """
        Create the notification message and sends it from the main Thread.


        :type t: (resource, host, port, token)
        :param t: the arguments of the notification message
        :return: the notification message
        """
        notification, resource = self._observe_layer.prepare_notification(t)
        if notification is not None:
            reactor.callFromThread(self._observe_layer.send_notification, (notification, resource))

    def prepare_notification_deletion(self, t):
        """
        Create the notification message for deleted resource and sends it from the main Thread.


        :type t: (resource, host, port, token)
        :param t: the arguments of the notification message
        :return: the notification message
        """
        notification, resource = self._observe_layer.prepare_notification_deletion(t)
        if notification is not None:
            reactor.callFromThread(self._observe_layer.send_notification, (notification, resource))

    def schedule_retrasmission(self, t):
        """
        Prepare retrasmission message and schedule it for the future.

        :type t: (Response, Resource) or Response
        :param t: the response and the resource interested in the retrasmission procedure
        """
        if isinstance(t, tuple):
            response, resource = t
        else:
            response = t
        host, port = response.destination
        if response.type == defines.inv_types['CON']:
            future_time = random.uniform(defines.ACK_TIMEOUT, (defines.ACK_TIMEOUT * defines.ACK_RANDOM_FACTOR))
            key = hash(str(host) + str(port) + str(response.mid))
            self.call_id[key] = (reactor.callLater(future_time, self.retransmit,
                                                   (t, host, port, future_time)), 1)

    def retransmit(self, t):
        """
        Retransmit the message and schedule retransmission for future if MAX_RETRANSMIT limit is not already reached.

        :param t: ((Response, Resource), host, port, future_time) or (Response, host, port, future_time)
        """
        log.msg("Retransmit")
        notification, host, port, future_time = t
        if isinstance(notification, tuple):
            response, resource = notification
        else:
            response = notification
            resource = None
        key = hash(str(host) + str(port) + str(response.mid))
        t = self.call_id.get(key)
        if t is None:
            return
        call_id, retransmit_count = t
        if retransmit_count < defines.MAX_RETRANSMIT and (not response.acknowledged and not response.rejected):
            retransmit_count += 1
            self.sent[key] = (response, time.time())
            self.send(response, host, port)
            future_time *= 2
            self.call_id[key] = (reactor.callLater(future_time, self.retransmit,
                                                   (notification, host, port, future_time)), retransmit_count)
        elif retransmit_count >= defines.MAX_RETRANSMIT and (not response.acknowledged and not response.rejected):
            print "Give up on Message " + str(response.mid)
            print "----------------------------------------"
        elif response.acknowledged or response.rejected:
            response.timeouted = False
            del self.call_id[key]
        else:
            response.timeouted = True
            if resource is not None:
                self._observe_layer.remove_observer(response, resource)
            del self.call_id[key]

    @staticmethod
    def send_error(request, response, error):
        """
        Send error messages as NON.

        :param request: the request that has generated the error
        :param response: the response message to be filled with the error
        :param error: the error type
        :return: the response
        """
        response.type = defines.inv_types['NON']
        response.code = defines.responses[error]
        response.token = request.token
        response.mid = request.mid
        return response