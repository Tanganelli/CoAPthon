import logging.config
import random
import socket
import threading

import os.path

from coapthon import defines
from coapthon.layers.blocklayer import BlockLayer
from coapthon.layers.messagelayer import MessageLayer
from coapthon.layers.observelayer import ObserveLayer
from coapthon.layers.requestlayer import RequestLayer
from coapthon.messages.message import Message
from coapthon.messages.request import Request
from coapthon.messages.response import Response
from coapthon.serializer import Serializer
from coapthon.utils import create_logging

__author__ = 'Giacomo Tanganelli'


logger = logging.getLogger(__name__)


class CoAP(object):
    def __init__(self, server, starting_mid, callback, sock=None):
        self._currentMID = starting_mid
        self._server = server
        self._callback = callback
        self.stopped = threading.Event()
        self.to_be_stopped = []

        self._messageLayer = MessageLayer(self._currentMID)
        self._blockLayer = BlockLayer()
        self._observeLayer = ObserveLayer()
        self._requestLayer = RequestLayer(self)

        # try:
        #     # legal
        #     socket.inet_aton(server[0])
        # except socket.error:
        #     # Not legal
        #     data = socket.getaddrinfo(server[0], server[1])
        #     self._server = (data[0], data[1])

        addrinfo = socket.getaddrinfo(self._server[0], None)[0]

        if sock is not None:
            self._socket = sock

        elif addrinfo[0] == socket.AF_INET:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        else:
            self._socket = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
            self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self._receiver_thread = threading.Thread(target=self.receive_datagram,
                                                 name=threading.current_thread().name+'-Receive_Datagram')

    def close(self):
        self._receiver_thread.join()
        self._socket.close()

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
            if transaction.request.type == defines.Types["CON"]:
                self._start_retransmission(transaction, transaction.request)

            self.send_datagram(transaction.request)
        elif isinstance(message, Message):
            message = self._observeLayer.send_empty(message)
            message = self._messageLayer.send_empty(None, None, message)
            self.send_datagram(message)

    def send_datagram(self, message):
        host, port = message.destination
        logger.debug("send_datagram - " + str(message))
        serializer = Serializer()
        message = serializer.serialize(message)

        self._socket.sendto(message, (host, port))

        if not self._receiver_thread.isAlive():
            self._receiver_thread.start()

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
                                                                 name=threading.current_thread().name+'-Retransmit',
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
                    logger.debug("retransmit Request")
                    retransmit_count += 1
                    future_time *= 2
                    self.send_datagram(message)

            if message.acknowledged or message.rejected:
                message.timeouted = False
            else:
                logger.warning("Give up on message {message}".format(message=message.line_print))
                message.timeouted = True

            try:
                self.to_be_stopped.remove(transaction.retransmit_stop)
            except ValueError:
                pass
            transaction.retransmit_stop = None
            transaction.retransmit_thread = None

    def receive_datagram(self):
        logger.debug("Start receiver Thread")
        while not self.stopped.isSet():
            self._socket.settimeout(1)
            try:
                datagram, addr = self._socket.recvfrom(1152)
            except socket.timeout:  # pragma: no cover
                continue
            except socket.error:  # pragma: no cover
                return
            else:  # pragma: no cover
                if len(datagram) == 0:
                    logger.debug("orderly shutdown on server end")
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
                if transaction is None:  # pragma: no cover
                    continue
                if send_ack:
                    self._send_ack(transaction)
                self._blockLayer.receive_response(transaction)
                if transaction.block_transfer:
                    transaction = self._messageLayer.send_request(transaction.request)
                    self.send_datagram(transaction.request)
                    continue
                elif transaction is None:  # pragma: no cover
                    self._send_rst(transaction)
                    return
                self._observeLayer.receive_response(transaction)
                if transaction.notification:  # pragma: no cover
                    ack = Message()
                    ack.type = defines.Types['ACK']
                    ack = self._messageLayer.send_empty(transaction, transaction.response, ack)
                    self.send_datagram(ack)
                    self._callback(transaction.response)
                else:
                    self._callback(transaction.response)
            elif isinstance(message, Message):
                self._messageLayer.receive_empty(message)

    def _send_ack(self, transaction):
        # Handle separate
        """
        Sends an ACK message for the response.

        :param transaction: transaction that holds the response
        """

        ack = Message()
        ack.type = defines.Types['ACK']

        if not transaction.response.acknowledged:
            ack = self._messageLayer.send_empty(transaction, transaction.response, ack)
            self.send_datagram(ack)

    def _send_rst(self, transaction):  # pragma: no cover
        # Handle separate
        """
        Sends an RST message for the response.

        :param transaction: transaction that holds the response
        """

        rst = Message()
        rst.type = defines.Types['RST']

        if not transaction.response.acknowledged:
            rst = self._messageLayer.send_empty(transaction, transaction.response, rst)
            self.send_datagram(rst)
