# from Bio import trie
import SocketServer
import os
import random
import socket
import threading
import time
from coapthon import defines
from coapthon.layer.blockwise import BlockwiseLayer
from coapthon.layer.message import MessageLayer
from coapthon.layer.observe import ObserveLayer
from coapthon.layer.request import RequestLayer
from coapthon.layer.resource import ResourceLayer
from coapthon.messages.message import Message
from coapthon.messages.request import Request
from coapthon.messages.response import Response
from coapthon.resources.resource import Resource
from coapthon.serializer import Serializer
import concurrent.futures
import logging
from coapthon.utils import Tree

__author__ = 'Giacomo Tanganelli'
__version__ = "2.0"

home = os.path.expanduser("~")
if not os.path.exists(home + "/.coapthon/"):
    os.makedirs(home + "/.coapthon/")


# logfile = DailyLogFile("CoAPthon_server.log", home + "/.coapthon/")
# # Now add an observer that logs to a file
# application = Application("CoAPthon_Server")
# application.setComponent(ILogObserver, FileLogObserver(logfile).emit)


class CoAP(object):
    def __init__(self, server_address, multicast=False):
        """
        Initialize the CoAP protocol

        """
        self.stop = False
        host, port = server_address
        ret = socket.getaddrinfo(host, port)
        family, socktype, proto, canonname, sockaddr = ret[0]

        self.stopped = threading.Event()
        self.stopped.clear()
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=10)
        self.executor_req = concurrent.futures.ThreadPoolExecutor(max_workers=10)
        self.received = {}
        self.sent = {}
        self.call_id = {}
        self.relation = {}
        self.blockwise = {}
        self._currentMID = random.randint(1, 1000)
        root = Resource('root', self, visible=False, observable=False, allow_children=True)
        root.path = '/'
        # self.root = trie.trie()
        self.root = Tree()
        self.root["/"] = root

        self.request_layer = RequestLayer(self)
        self.blockwise_layer = BlockwiseLayer(self)
        self.resource_layer = ResourceLayer(self)
        self.message_layer = MessageLayer(self)
        self.observe_layer = ObserveLayer(self)
        self.multicast = multicast
        self.timer_mid = threading.Timer(defines.EXCHANGE_LIFETIME, self.purge_mids)
        self.timer_mid.setDaemon(True)
        self.timer_mid.start()
        self.server_address = server_address

        if len(sockaddr) == 4:
            self._socket = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
        else:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        if self.multicast:
            # Set some options to make it multicast-friendly
            self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                    self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            except AttributeError:
                    pass  # Some systems don't support SO_REUSEPORT
            self._socket.setsockopt(socket.SOL_IP, socket.IP_MULTICAST_TTL, 20)
            self._socket.setsockopt(socket.SOL_IP, socket.IP_MULTICAST_LOOP, 1)

            # Bind to the port
            self._socket.bind(self.server_address)

            # Set some more multicast options
            interface = socket.gethostbyname(socket.gethostname())
            self._socket.setsockopt(socket.SOL_IP, socket.IP_MULTICAST_IF, socket.inet_aton(interface))
            self._socket.setsockopt(socket.SOL_IP, socket.IP_ADD_MEMBERSHIP, socket.inet_aton(self.server_address)
                                    + socket.inet_aton(interface))
        else:
            self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            self._socket.bind(self.server_address)

    def send(self, message, host, port):
        """
        Send the message

        :param message: the message to send
        :param host: destination host
        :param port: destination port
        """
        # print "Message send to " + host + ":" + str(port)
        # print "----------------------------------------"
        # print message
        # print "----------------------------------------"
        serializer = Serializer()
        message = serializer.serialize(message)

        self._socket.sendto(message, (host, port))

    def listen(self, timeout):
        while not self.stop:
            self._socket.settimeout(float(timeout))
            try:
                data, client_address = self._socket.recvfrom(4096)
            except socket.timeout:
                continue
            future = self.executor_req.submit(self.finish_request, (data, client_address))
            future.add_done_callback(self.done_callback)
        self._socket.close()

    def close(self):
        self.stop = True
        self.executor_req.shutdown(True)
        self.executor.shutdown(True)
        self.timer_mid.cancel()

    def done_callback(self, future):
        message, host, port = future.result(timeout=10.0)
        self.send(message, host, port)

    def finish_request(self, args):
        """
        Handler for received UDP datagram.

        :param data: the UDP datagram
        :param host: source host
        :param port: source port
        """
        data, client_address = args
        host = client_address[0]
        port = client_address[1]

        # logging.log(logging.INFO, "Datagram received from " + str(host) + ":" + str(port))
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
                response = self.request_layer.process(ret)
            else:
                response = ret
            self.schedule_retrasmission(message, response, None)
            # log.msg("Send Response")
            return response, host, port
        elif isinstance(message, Response):
            # log.err("Received response")
            rst = Message.new_rst(message)
            rst = self.message_layer.matcher_response(rst)
            # log.msg("Send RST")
            return rst, host, port
        elif isinstance(message, tuple):
            message, error = message
            response = Response()
            response.destination = (host, port)
            response.code = defines.responses[error]
            response = self.message_layer.reliability_response(message, response)
            response = self.message_layer.matcher_response(response)
            # log.msg("Send Error")
            return response, host, port
        elif message is not None:
            # ACK or RST
            # log.msg("Received ACK or RST")
            self.message_layer.handle_message(message)
            return None

    def purge_mids(self):
        """
        Delete messages which has been stored for more than EXCHANGE_LIFETIME.
        Executed in a thread.

        """
        # log.msg("Purge MIDs")
        while not self.stopped.isSet():
            time.sleep(defines.EXCHANGE_LIFETIME)
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
        print "Exit Purge MIDS"



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
        actual_path = ""
        i = 0
        for p in paths:
            i += 1
            actual_path += "/" + p
            try:
                res = self.root[actual_path]
            except KeyError:
                res = None
            if res is None:
                if len(paths) != i:
                    return False
                resource.path = actual_path
                self.root[actual_path] = resource
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

    def blockwise_response(self, request, response, resource):
        host, port = request.source
        key = hash(str(host) + str(port) + str(request.token))
        if key in self.blockwise:
            # Handle Blockwise transfer
            return self.blockwise_layer.handle_response(key, response, resource), resource
        if resource is not None and len(resource.payload) > defines.MAX_PAYLOAD \
                and request.code == defines.inv_codes["GET"]:
            self.blockwise_layer.start_block2(request)
            return self.blockwise_layer.handle_response(key, response, resource), resource
        return response, resource

    def notify(self, resource):
        """
        Finds the observers that must be notified about the update of the observed resource
        and invoke the notification procedure in different threads.

        :param resource: the node resource updated
        """
        commands = self.observe_layer.notify(resource)
        if commands is not None:
            for f, t in commands:
                self.executor.submit(f, t)

    def notify_deletion(self, resource):
        """
        Finds the observers that must be notified about the delete of the observed resource
        and invoke the notification procedure in different threads.

        :param resource: the node resource deleted
        """
        commands = self.observe_layer.notify_deletion(resource)
        if commands is not None:
            for f, t in commands:
                self.executor.submit(f, t)

    def remove_observers(self, path):
        """
        Remove all the observers of a resource and and invoke the notification procedure in different threads.

        :param path: the path of the deleted resource
        """
        commands = self.observe_layer.remove_observers(path)
        if commands is not None:
            for f, t in commands:
                self.executor.submit(f, t)

    def prepare_notification(self, t):
        """
        Create the notification message and sends it from the main Thread.

        :type t: (resource, request, response)
        :param t: the arguments of the notification message
        :return: the notification message
        """
        resource, request, notification = self.observe_layer.prepare_notification(t)
        if notification is not None:
            self.executor.submit(self.observe_layer.send_notification, (resource, request, notification))

    def prepare_notification_deletion(self, t):
        """
        Create the notification message for deleted resource and sends it from the main Thread.


        :type t: (resource, request, notification)
        :param t: the arguments of the notification message
        :return: the notification message
        """
        resource, request, notification = self.observe_layer.prepare_notification_deletion(t)
        if notification is not None:
            self.executor.submit(self.observe_layer.send_notification, (resource, request, notification))

    def schedule_retrasmission(self, request, response, resource):
        """
        Prepare retrasmission message and schedule it for the future.

        :param request:  the request
        :param response: the response
        :param resource: the resource
        """
        host, port = response.destination
        if response.type == defines.inv_types['CON']:
            future_time = random.uniform(defines.ACK_TIMEOUT, (defines.ACK_TIMEOUT * defines.ACK_RANDOM_FACTOR))
            key = hash(str(host) + str(port) + str(response.mid))
            self.call_id[key] = self.executor.submit(self.retransmit, (request, response, resource, future_time))

    def retransmit(self, t):
        """
        Retransmit the message and schedule retransmission for future if MAX_RETRANSMIT limit is not already reached.

        :param t: ((Response, Resource), host, port, future_time) or (Response, host, port, future_time)
        """
        # log.msg("Retransmit")
        request, response, resource, future_time = t
        time.sleep(future_time)
        host, port = response.destination

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
            self.call_id[key] = self.executor.submit(self.retransmit, (request, response, resource, future_time))
        elif retransmit_count >= defines.MAX_RETRANSMIT and (not response.acknowledged and not response.rejected):
            print "Give up on Message " + str(response.mid)
            print "----------------------------------------"
        elif response.acknowledged:
            response.timeouted = False
            del self.call_id[key]
        else:
            response.timeouted = True
            if resource is not None:
                self.observe_layer.remove_observer(resource, request, response)
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