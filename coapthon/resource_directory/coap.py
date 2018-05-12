import logging.config
import os
import random
import socket
import struct
import threading

from coapthon import defines
from coapthon.layers.blocklayer import BlockLayer
from coapthon.layers.messagelayer import MessageLayer
from coapthon.layers.observelayer import ObserveLayer
from rdrequestlayer import RdRequestLayer
from coapthon.layers.resourcelayer import ResourceLayer
from coapthon.messages.message import Message
from coapthon.messages.request import Request
from coapthon.messages.response import Response
from coapthon.resources.resource import Resource
from coapthon.serializer import Serializer
from coapthon.utils import Tree
from coapthon.utils import create_logging
from databaseManager import DatabaseManager


__author__ = 'Giacomo Tanganelli'


if not os.path.isfile("logging.conf"):
    create_logging()

logger = logging.getLogger(__name__)
logging.config.fileConfig("logging.conf", disable_existing_loggers=False)


class CoAP(object):
    """
    Implementation of the CoAP server
    """
    def __init__(self, server_address, multicast=False, starting_mid=None, sock=None, cb_ignore_listen_exception=None):
        """
        Initialize the server.

        :param server_address: Server address for incoming connections
        :param multicast: if the ip is a multicast address
        :param starting_mid: used for testing purposes
        :param sock: if a socket has been created externally, it can be used directly
        :param cb_ignore_listen_exception: Callback function to handle exception raised during the socket listen operation
        """
        self.stopped = threading.Event()
        self.stopped.clear()
        self.to_be_stopped = []
        self.purge = threading.Thread(target=self.purge)
        self.purge.start()

        self._messageLayer = MessageLayer(starting_mid)
        self._blockLayer = BlockLayer()
        self._observeLayer = ObserveLayer()
        self._requestLayer = RdRequestLayer(self)
        self.resourceLayer = ResourceLayer(self)

        # Resource directory
        root = Resource('root', self, visible=False, observable=False, allow_children=False)
        root.path = '/'
        self.root = Tree()
        self.root["/"] = root
        self._serializer = None

        self.server_address = server_address
        self.multicast = multicast
        self._cb_ignore_listen_exception = cb_ignore_listen_exception

        self.rd_stopped = threading.Event()
        self.rd_stopped.clear()
        self.rd_lt_manager = threading.Thread(target=self.manage_lifetime)
        self.rd_lt_manager.start()

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
                if len(client_address) > 2:
                    client_address = (client_address[0], client_address[1])
            except socket.timeout:
                continue
            except Exception as e:
                if self._cb_ignore_listen_exception is not None and callable(self._cb_ignore_listen_exception):
                    if self._cb_ignore_listen_exception(e, self):
                        continue
                raise
            try:
                serializer = Serializer()
                message = serializer.deserialize(data, client_address)
                if isinstance(message, int):
                    logger.error("receive_datagram - BAD REQUEST")

                    rst = Message()
                    rst.destination = client_address
                    rst.type = defines.Types["RST"]
                    rst.code = message
                    rst.mid = self._messageLayer.fetch_mid()
                    self.send_datagram(rst)
                    continue

                logger.debug("receive_datagram - " + str(message))
                if isinstance(message, Request):
                    transaction = self._messageLayer.receive_request(message)
                    if transaction.request.duplicated and transaction.completed:
                        logger.debug("message duplicated, transaction completed")
                        if transaction.response is not None:
                            self.send_datagram(transaction.response)
                        continue
                    elif transaction.request.duplicated and not transaction.completed:
                        logger.debug("message duplicated, transaction NOT completed")
                        self._send_ack(transaction)
                        continue
                    args = (transaction, )
                    t = threading.Thread(target=self.receive_request, args=args)
                    t.start()
                # self.receive_datagram(data, client_address)
                elif isinstance(message, Response):
                    logger.error("Received response from %s", message.source)

                else:  # is Message
                    transaction = self._messageLayer.receive_empty(message)
                    if transaction is not None:
                        with transaction:
                            self._blockLayer.receive_empty(message, transaction)
                            self._observeLayer.receive_empty(message, transaction)

            except RuntimeError:
                logger.exception("Exception with Executor")
        self._socket.close()

    def close(self):
        """
        Stop the server.

        """
        logger.info("Stop server")
        self.rd_stopped.set()
        self.stopped.set()
        for event in self.to_be_stopped:
            event.set()

    def receive_request(self, transaction):
        """
        Handle requests coming from the udp socket.

        :param transaction: the transaction created to manage the request
        """

        with transaction:

            transaction.separate_timer = self._start_separate_timer(transaction)

            self._blockLayer.receive_request(transaction)

            if transaction.block_transfer:
                self._stop_separate_timer(transaction.separate_timer)
                self._messageLayer.send_response(transaction)
                self.send_datagram(transaction.response)
                return

            self._observeLayer.receive_request(transaction)

            self._requestLayer.receive_request(transaction)

            if transaction.resource is not None and transaction.resource.changed:
                self.notify(transaction.resource)
                transaction.resource.changed = False
            elif transaction.resource is not None and transaction.resource.deleted:
                self.notify(transaction.resource)
                transaction.resource.deleted = False

            self._observeLayer.send_response(transaction)

            self._blockLayer.send_response(transaction)

            self._stop_separate_timer(transaction.separate_timer)

            self._messageLayer.send_response(transaction)

            if transaction.response is not None:
                if transaction.response.type == defines.Types["CON"]:
                    self._start_retransmission(transaction, transaction.response)
                self.send_datagram(transaction.response)

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
            if self.multicast:
                self._unicast_socket.sendto(message, (host, port))
            else:
                self._socket.sendto(message, (host, port))

    def add_resource(self, path, resource):
        """
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

    def remove_resource(self, path):
        """
        Helper function to remove resources.

        :param path: the path for the unwanted resource
        :rtype : the removed object
        """

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
        if res is not None:
            del(self.root[actual_path])
        return res

    def _start_retransmission(self, transaction, message):
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
                if transaction.retransmit_stop is not None:
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
        # TODO handle mutex on transaction
        if not transaction.request.acknowledged and transaction.request.type == defines.Types["CON"]:
            ack = self._messageLayer.send_empty(transaction, transaction.request, ack)
            self.send_datagram(ack)

    def notify(self, resource):
        """
        Notifies the observers of a certain resource.

        :param resource: the resource
        """
        observers = self._observeLayer.notify(resource)
        logger.debug("Notify")
        for transaction in observers:
            with transaction:
                transaction.response = None
                transaction = self._requestLayer.receive_request(transaction)
                transaction = self._observeLayer.send_response(transaction)
                transaction = self._blockLayer.send_response(transaction)
                transaction = self._messageLayer.send_response(transaction)
                if transaction.response is not None:
                    if transaction.response.type == defines.Types["CON"]:
                        self._start_retransmission(transaction, transaction.response)

                    self.send_datagram(transaction.response)

    def manage_lifetime(self):
        """
        Every 1800 seconds calls the function to delete the expired resources.
        """
        while not self.rd_stopped.isSet():
            db = DatabaseManager()
            db.delete_expired()
            self.rd_stopped.wait(timeout=1800)
