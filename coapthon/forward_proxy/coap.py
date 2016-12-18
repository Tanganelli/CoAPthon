import logging.config
import random
import socket
import struct
import threading

import os

from coapthon import defines
from coapthon.layers.blocklayer import BlockLayer
from coapthon.layers.cachelayer import CacheLayer
from coapthon.layers.forwardLayer import ForwardLayer
from coapthon.layers.messagelayer import MessageLayer
from coapthon.layers.observelayer import ObserveLayer
from coapthon.layers.resourcelayer import ResourceLayer
from coapthon.messages.message import Message
from coapthon.messages.request import Request
from coapthon.resources.resource import Resource
from coapthon.serializer import Serializer
from coapthon.utils import Tree, create_logging

__author__ = 'Giacomo Tanganelli'

if not os.path.isfile("logging.conf"):
    create_logging()

logger = logging.getLogger(__name__)
logging.config.fileConfig("logging.conf", disable_existing_loggers=False)


class CoAP(object):
    def __init__(self, server_address, multicast=False, starting_mid=None, cache=False):

        self.stopped = threading.Event()
        self.stopped.clear()
        self.to_be_stopped = []
        self.purge = threading.Thread(target=self.purge)
        self.purge.start()
        self.cache_enable = cache

        self._messageLayer = MessageLayer(starting_mid)
        self._blockLayer = BlockLayer()
        self._observeLayer = ObserveLayer()

        if self.cache_enable:
            self._cacheLayer = CacheLayer(defines.FORWARD_PROXY)
        else:
            self._cacheLayer = None

        self._forwardLayer = ForwardLayer(self)
        self.resourceLayer = ResourceLayer(self)

        # Resource directory
        root = Resource('root', self, visible=False, observable=False, allow_children=True)
        root.path = '/'
        self.root = Tree()
        self.root["/"] = root
        self._serializer = None

        self.server_address = server_address
        self.multicast = multicast

        addrinfo = socket.getaddrinfo(self.server_address[0], None)[0]

        if self.multicast: # pragma: no cover

            # Create a socket
            self._socket = socket.socket(addrinfo[1], socket.SOCK_DGRAM)

            # Allow multiple copies of this program on one machine
            # (not strictly needed)
            self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            # Bind it to the port
            self._socket.bind(('', self.server_address[1]))

            group_bin = socket.inet_pton(addrinfo[1], addrinfo[4][0])
            # Join group
            if addrinfo[0] == socket.AF_INET: # IPv4
                mreq = group_bin + struct.pack('=I', socket.INADDR_ANY)
                self._socket.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
            else:
                mreq = group_bin + struct.pack('@I', 0)
                self._socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_JOIN_GROUP, mreq)

        else:
            if addrinfo[0] == socket.AF_INET: # IPv4
                self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            else:
                self._socket = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
                self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            self._socket.bind(self.server_address)

    def purge(self):
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
                print "Exception with Executor"
        print "closing socket"
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
        Receive datagram from the udp socket.

        :rtype : Message
        """
        data, client_address = args

        print "receiving datagram"

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
                    print transaction.request
                    transaction = self._forwardLayer.receive_request(transaction)
                    print transaction.response

                transaction = self._observeLayer.send_response(transaction)

                transaction = self._blockLayer.send_response(transaction)

                transaction = self._cacheLayer.send_response(transaction)
            else:
                transaction = self._forwardLayer.receive_request(transaction)

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

        else:  # is Response
            logger.error("Received response from %s", message.source)

    def send_datagram(self, message):
        """

        :type message: Message
        :param message:
        """
        if not self.stopped.isSet():
            host, port = message.destination
            logger.debug("send_datagram - " + str(message))
            serializer = Serializer()
            message = serializer.serialize(message)

            self._socket.sendto(message, (host, port))

    def _start_retrasmission(self, transaction, message):
        """

        :type transaction: Transaction
        :param transaction:
        :type message: Message
        :param message:
        :rtype : Future
        """
        if message.type == defines.Types['CON']:
            future_time = random.uniform(defines.ACK_TIMEOUT, (defines.ACK_TIMEOUT * defines.ACK_RANDOM_FACTOR))
            transaction.retransmit_thread = threading.Thread(target=self._retransmit,
                                                             args=(transaction, message, future_time, 0))
            transaction.retransmit_stop = threading.Event()
            self.to_be_stopped.append(transaction.retransmit_stop)
            transaction.retransmit_thread.start()

    def _retransmit(self, transaction, message, future_time, retransmit_count):
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

        :type transaction: Transaction
        :param transaction:
        :rtype : Timer
        """
        t = threading.Timer(defines.ACK_TIMEOUT, self._send_ack, (transaction,))
        t.start()
        return t

    @staticmethod
    def _stop_separate_timer(timer):
        """

        :type timer: Timer
        :param timer: The timer object
        """
        timer.cancel()

    def _send_ack(self, transaction):
        # Handle separate
        """
        Sends an ACK message for the request.

        :param transaction: The transaction to be acknowledged
        """

        ack = Message()
        ack.type = defines.Types['ACK']

        if not transaction.request.acknowledged:
            ack = self._messageLayer.send_empty(transaction, transaction.request, ack)
            self.send_datagram(ack)