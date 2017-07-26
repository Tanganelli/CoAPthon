import logging.config
import random
import socket
import struct
import threading
import xml.etree.ElementTree as ElementTree

import os
import re

from coapthon import defines
from coapthon.client.helperclient import HelperClient
from coapthon.layers.blocklayer import BlockLayer
from coapthon.layers.cachelayer import CacheLayer
from coapthon.layers.forwardLayer import ForwardLayer
from coapthon.layers.messagelayer import MessageLayer
from coapthon.layers.observelayer import ObserveLayer
from coapthon.layers.resourcelayer import ResourceLayer
from coapthon.messages.message import Message
from coapthon.messages.request import Request
from coapthon.resources.remoteResource import RemoteResource
from coapthon.resources.resource import Resource
from coapthon.serializer import Serializer
from coapthon.utils import Tree, create_logging

__author__ = 'Giacomo Tanganelli'


if not os.path.isfile("logging.conf"):
    create_logging()

logger = logging.getLogger(__name__)
logging.config.fileConfig("logging.conf", disable_existing_loggers=False)


class CoAP(object):
    """
    Implementation of the Reverse Proxy
    """
    def __init__(self, server_address, xml_file, multicast=False, starting_mid=None, cache=False, sock=None):
        """
        Initialize the Reverse Proxy.

        :param server_address: Server address for incoming connections
        :param xml_file: the xml file that describe remote servers
        :param multicast: if the ip is a multicast address
        :param starting_mid: used for testing purposes
        :param cache: if a cache must be used
        :param sock: if a socket has been created externally, it can be used directly
        """
        self.stopped = threading.Event()
        self.stopped.clear()
        self.to_be_stopped = []
        self.purge = threading.Thread(target=self.purge)
        self.purge.start()

        self._messageLayer = MessageLayer(starting_mid)
        self._blockLayer = BlockLayer()
        self._observeLayer = ObserveLayer()

        self._forwardLayer = ForwardLayer(self)
        self.resourceLayer = ResourceLayer(self)
        self.cache_enable = cache
        if self.cache_enable:
            self._cacheLayer = CacheLayer(defines.REVERSE_PROXY)
        else:
            self._cacheLayer = None

        # Resource directory
        root = Resource('root', self, visible=False, observable=False, allow_children=True)
        root.path = '/'
        self.root = Tree()
        self.root["/"] = root
        self._serializer = None

        self.server_address = server_address
        self.multicast = multicast
        self.file_xml = xml_file
        self._mapping = {}

        addrinfo = socket.getaddrinfo(self.server_address[0], None)[0]

        if sock is not None:

            # Use given socket, could be a DTLS socket
            self._socket = sock

        elif self.multicast:  # pragma: no cover

            # Create a socket
            # self._socket.setsockopt(socket.SOL_IP, socket.IP_MULTICAST_TTL, 255)
            # self._socket.setsockopt(socket.SOL_IP, socket.IP_MULTICAST_LOOP, 1)

            # Join group
            if addrinfo[0] == socket.AF_INET:  # IPv4
                self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)

                # Allow multiple copies of this program on one machine
                # (not strictly needed)
                self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                self._socket.bind((defines.ALL_COAP_NODES, self.server_address[1]))
                mreq = struct.pack("4sl", socket.inet_aton(defines.ALL_COAP_NODES), socket.INADDR_ANY)
                self._socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
                self._unicast_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                self._unicast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                self._unicast_socket.bind(self.server_address)
            else:
                self._socket = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM, socket.IPPROTO_UDP)

                # Allow multiple copies of this program on one machine
                # (not strictly needed)
                self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                self._socket.bind((defines.ALL_COAP_NODES_IPV6, self.server_address[1]))

                addrinfo_multicast = socket.getaddrinfo(defines.ALL_COAP_NODES_IPV6, 5683)[0]
                group_bin = socket.inet_pton(socket.AF_INET6, addrinfo_multicast[4][0])
                mreq = group_bin + struct.pack('@I', 0)
                self._socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_JOIN_GROUP, mreq)
                self._unicast_socket = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
                self._unicast_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                self._unicast_socket.bind(self.server_address)
        else:
            if addrinfo[0] == socket.AF_INET:  # IPv4
                self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            else:
                self._socket = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
                self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            self._socket.bind(self.server_address)

            self.parse_config()

    def parse_config(self):
        """
        Parse the xml file with remote servers and discover resources on each found server.
        """
        tree = ElementTree.parse(self.file_xml)
        root = tree.getroot()
        for server in root.findall('server'):
            destination = server.text
            name = server.get("name")
            self.discover_remote(destination, name)

    def discover_remote(self, destination, name):
        """
        Discover resources on remote servers.

        :param destination: the remote server (ip, port)
        :type destination: tuple
        :param name: the name of the remote server
        :type name: String
        """
        assert (isinstance(destination, str))
        if destination.startswith("["):
            split = destination.split("]", 1)
            host = split[0][1:]
            port = int(split[1][1:])
        else:
            split = destination.split(":", 1)
            host = split[0]
            port = int(split[1])
        server = (host, port)
        client = HelperClient(server)
        response = client.discover()
        client.stop()
        self.discover_remote_results(response, name)

    def discover_remote_results(self, response, name):
        """
        Create a new remote server resource for each valid discover response.

        :param response: the response to the discovery request
        :param name: the server name
        """
        host, port = response.source

        if response.code == defines.Codes.CONTENT.number:
            resource = Resource('server', self, visible=True, observable=False, allow_children=True)
            self.add_resource(name, resource)
            self._mapping[name] = (host, port)
            self.parse_core_link_format(response.payload, name, (host, port))
        else:
            logger.error("Server: " + response.source + " isn't valid.")

    def parse_core_link_format(self, link_format, base_path, remote_server):
        """
        Parse discovery results.

        :param link_format: the payload of the response to the discovery request
        :param base_path: the base path used to create child resources discovered on the remote server
        :param remote_server: the (ip, port) of the remote server
        """
        while len(link_format) > 0:
            pattern = "<([^>]*)>;"
            result = re.match(pattern, link_format)
            path = result.group(1)
            path = path.split("/")
            path = path[1:][0]
            link_format = link_format[result.end(1) + 2:]
            pattern = "([^<,])*"
            result = re.match(pattern, link_format)
            attributes = result.group(0)
            dict_att = {}
            if len(attributes) > 0:
                attributes = attributes.split(";")
                for att in attributes:
                    a = att.split("=")
                    if len(a) > 1:
                        dict_att[a[0]] = a[1]
                    else:
                        dict_att[a[0]] = a[0]
                link_format = link_format[result.end(0) + 1:]
            # TODO handle observing
            resource = RemoteResource('server', remote_server, path, coap_server=self, visible=True, observable=False,
                                      allow_children=True)
            resource.attributes = dict_att
            self.add_resource(base_path + "/" + path, resource)

        logger.info(self.root.dump())

    def purge(self):
        """
        Clean old transactions
        """
        while not self.stopped.isSet():
            self.stopped.wait(timeout=defines.EXCHANGE_LIFETIME)
            self._messageLayer.purge()

    def listen(self, timeout=10):
        """
        Listen for incoming messages. Timeout is used to check if the server must be switched off.

        :param timeout: Socket Timeout in seconds
        """
        self._socket.settimeout(float(timeout))
        while not self.stopped.isSet():
            try:
                data, client_address = self._socket.recvfrom(4096)
            except socket.timeout:
                continue
            try:

                self.receive_datagram((data, client_address))
            except RuntimeError:
                logger.exception("Exception with Executor")
        self._socket.close()

    def close(self):
        """
        Stop the server.

        """
        logger.info("Stop server")
        self.stopped.set()
        for event in self.to_be_stopped:
            event.set()
        self._socket.close()

    def receive_datagram(self, args):
        """
        Handle messages coming from the udp socket.

        :param args: (data, client_address)
        """
        data, client_address = args

        serializer = Serializer()
        message = serializer.deserialize(data, client_address)
        if isinstance(message, int):
            logger.error("receive_datagram - BAD REQUEST")

            rst = Message()
            rst.destination = client_address
            rst.type = defines.Types["RST"]
            rst.code = message
            self.send_datagram(rst)
            return
        logger.debug("receive_datagram - " + str(message))
        if isinstance(message, Request):

            transaction = self._messageLayer.receive_request(message)

            if transaction.request.duplicated and transaction.completed:
                logger.debug("message duplicated,transaction completed")
                transaction = self._observeLayer.send_response(transaction)
                transaction = self._blockLayer.send_response(transaction)
                transaction = self._messageLayer.send_response(transaction)
                self.send_datagram(transaction.response)
                return
            elif transaction.request.duplicated and not transaction.completed:
                logger.debug("message duplicated,transaction NOT completed")
                self._send_ack(transaction)
                return

            transaction.separate_timer = self._start_separate_timer(transaction)

            transaction = self._blockLayer.receive_request(transaction)

            if transaction.block_transfer:
                self._stop_separate_timer(transaction.separate_timer)
                transaction = self._messageLayer.send_response(transaction)
                self.send_datagram(transaction.response)
                return

            transaction = self._observeLayer.receive_request(transaction)

            """
            call to the cache layer to check if there's a cached response for the request
            if not, call the forward layer
            """
            if self._cacheLayer is not None:
                transaction = self._cacheLayer.receive_request(transaction)

                if transaction.cacheHit is False:
                    logger.debug(transaction.request)
                    transaction = self._forwardLayer.receive_request_reverse(transaction)
                    logger.debug(transaction.response)

                transaction = self._observeLayer.send_response(transaction)

                transaction = self._blockLayer.send_response(transaction)

                transaction = self._cacheLayer.send_response(transaction)
            else:
                transaction = self._forwardLayer.receive_request_reverse(transaction)

                transaction = self._observeLayer.send_response(transaction)

                transaction = self._blockLayer.send_response(transaction)

            self._stop_separate_timer(transaction.separate_timer)

            transaction = self._messageLayer.send_response(transaction)

            if transaction.response is not None:
                if transaction.response.type == defines.Types["CON"]:
                    self._start_retrasmission(transaction, transaction.response)
                self.send_datagram(transaction.response)

        elif isinstance(message, Message):
            transaction = self._messageLayer.receive_empty(message)
            if transaction is not None:
                transaction = self._blockLayer.receive_empty(message, transaction)
                self._observeLayer.receive_empty(message, transaction)

        else:  # pragma: no cover
            logger.error("Received response from %s", message.source)

    def send_datagram(self, message):
        """
        Send a message through the udp socket.

        :type message: Message
        :param message: the message to send
        """
        if not self.stopped.isSet():
            host, port = message.destination
            logger.debug("send_datagram - " + str(message))
            serializer = Serializer()
            message = serializer.serialize(message)

            self._socket.sendto(message, (host, port))

    def add_resource(self, path, resource):
        """"
        Helper function to add resources to the resource directory during server initialization.

        :param path: the path for the new created resource
        :type resource: Resource
        :param resource: the resource to be added
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

    def _start_retrasmission(self, transaction, message):
        """
        Start the retransmission task.

        :type transaction: Transaction
        :param transaction: the transaction that owns the message that needs retransmission
        :type message: Message
        :param message: the message that needs the retransmission task
        """
        with transaction:
            if message.type == defines.Types['CON']:
                future_time = random.uniform(defines.ACK_TIMEOUT, (defines.ACK_TIMEOUT * defines.ACK_RANDOM_FACTOR))
                transaction.retransmit_thread = threading.Thread(target=self._retransmit,
                                                                 args=(transaction, message, future_time, 0))
                transaction.retransmit_stop = threading.Event()
                self.to_be_stopped.append(transaction.retransmit_stop)
                transaction.retransmit_thread.start()

    def _retransmit(self, transaction, message, future_time, retransmit_count):
        """
        Thread function to retransmit the message in the future

        :param transaction: the transaction that owns the message that needs retransmission
        :param message: the message that needs the retransmission task
        :param future_time: the amount of time to wait before a new attempt
        :param retransmit_count: the number of retransmissions
        """
        with transaction:
            while retransmit_count < defines.MAX_RETRANSMIT and (not message.acknowledged and not message.rejected) \
                    and not self.stopped.isSet():
                transaction.retransmit_stop.wait(timeout=future_time)
                if not message.acknowledged and not message.rejected and not self.stopped.isSet():
                    retransmit_count += 1
                    future_time *= 2
                    self.send_datagram(message)

            if message.acknowledged or message.rejected:
                message.timeouted = False
            else:
                logger.warning("Give up on message {message}".format(message=message.line_print))
                message.timeouted = True
                if message.observe is not None:
                    self._observeLayer.remove_subscriber(message)

            try:
                self.to_be_stopped.remove(transaction.retransmit_stop)
            except ValueError:
                pass
            transaction.retransmit_stop = None
            transaction.retransmit_thread = None

    def _start_separate_timer(self, transaction):
        """
        Start a thread to handle separate mode.

        :type transaction: Transaction
        :param transaction: the transaction that is in processing
        :rtype : the Timer object
        """
        t = threading.Timer(defines.ACK_TIMEOUT, self._send_ack, (transaction,))
        t.start()
        return t

    @staticmethod
    def _stop_separate_timer(timer):
        """
        Stop the separate Thread if an answer has been already provided to the client.

        :param timer: The Timer object
        """
        timer.cancel()

    def _send_ack(self, transaction):
        """
        Sends an ACK message for the request.

        :param transaction: the transaction that owns the request
        """

        ack = Message()
        ack.type = defines.Types['ACK']

        if not transaction.request.acknowledged:
            ack = self._messageLayer.send_empty(transaction, transaction.request, ack)
            self.send_datagram(ack)
