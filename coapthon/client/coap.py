import logging
import logging.config
import socket
import threading
from coapthon.messages.message import Message
from coapthon.messages.response import Response
from coapthon import defines
from coapthon.layers.blocklayer import BlockLayer
from coapthon.layers.messagelayer import MessageLayer
from coapthon.layers.observelayer import ObserveLayer
from coapthon.layers.requestlayer import RequestLayer
from coapthon.messages.request import Request
from coapthon.serializer import Serializer

__author__ = 'giacomo'

logger = logging.getLogger(__name__)
logging.config.fileConfig("logging.conf", disable_existing_loggers=False)


class CoAP(object):
    def __init__(self, server, starting_mid, callback):
        self._currentMID = starting_mid
        self._server = server
        self._callback = callback
        self.stopped = threading.Event()

        self._messageLayer = MessageLayer(self._currentMID)
        self._blockLayer = BlockLayer()
        self._observeLayer = ObserveLayer()
        self._requestLayer = RequestLayer(self)

        try:
            # legal
            socket.inet_aton(server[0])
        except socket.error:
            # Not legal
            data = socket.getaddrinfo(server[0], server[1])
            self._server = (data[0], data[1])

        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._receiver_thread = threading.Thread(target=self.receive_datagram)
        self._receiver_thread.start()

    @property
    def current_mid(self):
        return self._currentMID

    @current_mid.setter
    def current_mid(self, c):
        assert isinstance(c, int)
        self._currentMID = c

    def send_message(self, message):

        if isinstance(message, Request):
            request = self._requestLayer.send_request(message)
            request = self._observeLayer.send_request(request)
            request = self._blockLayer.send_request(request)
            transaction = self._messageLayer.send_request(request)
            self.send_datagram(transaction.request)
        elif isinstance(message, Message):
            message = self._observeLayer.send_empty(message)
            message = self._blockLayer.send_empty(message)
            message = self._messageLayer.send_empty(None, None, message)
            self.send_datagram(message)

    def send_datagram(self, message):
        host, port = message.destination
        logger.debug("send_datagram - " + str(message))
        serializer = Serializer()
        message = serializer.serialize(message)

        self._socket.sendto(message, (host, port))

    def receive_datagram(self):
        logger.debug("Start receiver Thread")
        while not self.stopped.isSet():
            self._socket.settimeout(1)
            try:
                datagram, addr = self._socket.recvfrom(1152)
            except socket.timeout, e:
                err = e.args[0]
                # this next if/else is a bit redundant, but illustrates how the
                # timeout exception is setup
                if err == 'timed out':
                    continue
                else:
                    print e
                    return
            except socket.error, e:
                # Something else happened, handle error, exit, etc.
                print e
                return
            else:
                if len(datagram) == 0:
                    print 'orderly shutdown on server end'
                    return

            serializer = Serializer()

            try:
                host, port = addr
            except ValueError:
                host, port, tmp1, tmp2 = addr

            source = (host, port)

            message = serializer.deserialize(datagram, source)

            if isinstance(message, Response):
                transaction, send_ack = self._messageLayer.receive_response(message)
                if send_ack:
                    self._send_ack(transaction)
                transaction = self._blockLayer.receive_response(transaction)
                if transaction.block_transfer:
                    transaction = self._messageLayer.send_request(transaction.request)
                    self.send_datagram(transaction.request)
                    continue
                transaction = self._observeLayer.receive_response(transaction)
                if transaction.notification:
                    ack = Message()
                    ack.type = defines.Types['ACK']
                    ack = self._messageLayer.send_empty(transaction, transaction.response, ack)
                    self.send_datagram(ack)
                    self._callback(transaction.response)
                else:
                    self._callback(transaction.response)
            elif isinstance(message, Message):
                transaction = self._messageLayer.receive_empty(message)

    def _send_ack(self, transaction):
        # Handle separate
        """
        Sends an ACK message for the request.

        :param request: [request, sleep_time] or request
        """

        ack = Message()
        ack.type = defines.Types['ACK']

        if not transaction.response.acknowledged:
            ack = self._messageLayer.send_empty(transaction, transaction.response, ack)
            self.send_datagram(ack)
