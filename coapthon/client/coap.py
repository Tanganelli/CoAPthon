import logging.config
import os
import random
import socket
import threading
import time

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


if not os.path.isfile("logging.conf"):
    create_logging()

logger = logging.getLogger(__name__)
logging.config.fileConfig("logging.conf", disable_existing_loggers=False)


class CoAP(object):
    """
    Client class to perform requests to remote servers.
    """
    def __init__(self, server, starting_mid, callback, sock=None, cb_ignore_read_exception=None, cb_ignore_write_exception=None):
        """
        Initialize the client.

        :param server: Server address for incoming connections
        :param callback:the callback function to be invoked when a response is received
        :param starting_mid: used for testing purposes
        :param sock: if a socket has been created externally, it can be used directly
        :param cb_ignore_read_exception: Callback function to handle exception raised during the socket read operation
        :param cb_ignore_write_exception: Callback function to handle exception raised during the socket write operation        
        """
        self._currentMID = starting_mid
        self._server = server
        self._callback = callback
        self._cb_ignore_read_exception = cb_ignore_read_exception
        self._cb_ignore_write_exception = cb_ignore_write_exception
        self.stopped = threading.Event()
        self.to_be_stopped = []

        self._messageLayer = MessageLayer(self._currentMID)
        self._blockLayer = BlockLayer()
        self._observeLayer = ObserveLayer()
        self._requestLayer = RequestLayer(self)

        addrinfo = socket.getaddrinfo(self._server[0], None)[0]

        if sock is not None:
            self._socket = sock

        elif addrinfo[0] == socket.AF_INET:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        else:
            self._socket = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)
            self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self._receiver_thread = None

    def close(self):
        """
        Stop the client.

        """
        self.stopped.set()
        for event in self.to_be_stopped:
            event.set()
        if self._receiver_thread is not None:
            self._receiver_thread.join()
        try:
            # Python does not close the OS FD on socket.close()
            # Ensure OS socket is closed with shutdown to prevent FD leak
            self._socket.shutdown(socket.SHUT_RDWR)
        except socket.error:
            pass
        self._socket.close()

    @property
    def current_mid(self):
        """
        Return the current MID.

        :return: the current mid
        """
        return self._currentMID

    @current_mid.setter
    def current_mid(self, c):
        """
        Set the current MID.

        :param c: the mid to set
        """
        assert isinstance(c, int)
        self._currentMID = c

    def send_message(self, message):
        """
        Prepare a message to send on the UDP socket. Eventually set retransmissions.

        :param message: the message to send
        """
        if isinstance(message, Request):
            request = self._requestLayer.send_request(message)
            request = self._observeLayer.send_request(request)
            request = self._blockLayer.send_request(request)
            transaction = self._messageLayer.send_request(request)
            self.send_datagram(transaction.request)
            if transaction.request.type == defines.Types["CON"]:
                self._start_retransmission(transaction, transaction.request)
        elif isinstance(message, Message):
            message = self._observeLayer.send_empty(message)
            message = self._messageLayer.send_empty(None, None, message)
            self.send_datagram(message)

    def end_observation(self, token):
        """
        Remove an observation token from our records.

        :param token: the token for the observation
        """
        dummy = Message()
        dummy.token = token
        dummy.destination = self._server
        self._observeLayer.remove_subscriber(dummy)

    @staticmethod
    def _wait_for_retransmit_thread(transaction):
        """
        Only one retransmit thread at a time, wait for other to finish
        
        """
        if hasattr(transaction, 'retransmit_thread'):
            while transaction.retransmit_thread is not None:
                logger.debug("Waiting for retransmit thread to finish ...")
                time.sleep(0.01)
                continue

    def _send_block_request(self, transaction):
        """
        A former request resulted in a block wise transfer. With this method, the block wise transfer
        will be continued, including triggering of the retry mechanism.
        
        :param transaction: The former transaction including the request which should be continued.
        """
        transaction = self._messageLayer.send_request(transaction.request)
        # ... but don't forget to reset the acknowledge flag
        transaction.request.acknowledged = False
        self.send_datagram(transaction.request)
        if transaction.request.type == defines.Types["CON"]:
            self._start_retransmission(transaction, transaction.request)

    def send_datagram(self, message):
        """
        Send a message over the UDP socket.

        :param message: the message to send
        """
        host, port = message.destination
        logger.debug("send_datagram - " + str(message))
        serializer = Serializer()
        raw_message = serializer.serialize(message)

        try:
            self._socket.sendto(raw_message, (host, port))
        except Exception as e:
            if self._cb_ignore_write_exception is not None and callable(self._cb_ignore_write_exception):
                if not self._cb_ignore_write_exception(e, self):
                    raise

        if self._receiver_thread is None or not self._receiver_thread.isAlive():
            self._receiver_thread = threading.Thread(target=self.receive_datagram)
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
                transaction.retransmit_stop = threading.Event()
                self.to_be_stopped.append(transaction.retransmit_stop)
                transaction.retransmit_thread = threading.Thread(target=self._retransmit,
                                                                 name=str('%s-Retry-%d' % (threading.current_thread().name, message.mid)),
                                                                 args=(transaction, message, future_time, 0))
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
            logger.debug("retransmit loop ... enter")
            while retransmit_count <= defines.MAX_RETRANSMIT \
                    and (not message.acknowledged and not message.rejected) \
                    and not transaction.retransmit_stop.isSet():
                transaction.retransmit_stop.wait(timeout=future_time)
                if not message.acknowledged and not message.rejected and not transaction.retransmit_stop.isSet():
                    retransmit_count += 1
                    future_time *= 2
                    if retransmit_count < defines.MAX_RETRANSMIT:
                        logger.debug("retransmit loop ... retransmit Request")
                        self.send_datagram(message)

            if message.acknowledged or message.rejected:
                message.timeouted = False
            else:
                logger.warning("Give up on message {message}".format(message=message.line_print))
                message.timeouted = True

                # Inform the user, that nothing was received
                self._callback(message)

            try:
                self.to_be_stopped.remove(transaction.retransmit_stop)
            except ValueError:
                pass
            transaction.retransmit_stop = None
            transaction.retransmit_thread = None

            logger.debug("retransmit loop ... exit")

    def receive_datagram(self):
        """
        Receive datagram from the UDP socket and invoke the callback function.
        """
        logger.debug("Start receiver Thread")
        while not self.stopped.isSet():
            self._socket.settimeout(0.1)
            try:
                datagram, addr = self._socket.recvfrom(1152)
            except socket.timeout:  # pragma: no cover
                continue
            except Exception as e:  # pragma: no cover
                if self._cb_ignore_read_exception is not None and callable(self._cb_ignore_read_exception):
                    if self._cb_ignore_read_exception(e, self):
                        continue
                return
            else:  # pragma: no cover
                if len(datagram) == 0:
                    logger.debug("Exiting receiver Thread due to orderly shutdown on server end")
                    return

            serializer = Serializer()

            try:
                host, port = addr
            except ValueError:
                host, port, tmp1, tmp2 = addr

            source = (host, port)

            message = serializer.deserialize(datagram, source)

            if isinstance(message, Response):
                logger.debug("receive_datagram - " + str(message))
                transaction, send_ack = self._messageLayer.receive_response(message)
                if transaction is None:  # pragma: no cover
                    continue
                self._wait_for_retransmit_thread(transaction)
                if send_ack:
                    self._send_ack(transaction)
                self._blockLayer.receive_response(transaction)
                if transaction.block_transfer:
                    self._send_block_request(transaction)
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

        logger.debug("Exiting receiver Thread due to request")

    def _send_ack(self, transaction):
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
        """
        Sends an RST message for the response.

        :param transaction: transaction that holds the response
        """

        rst = Message()
        rst.type = defines.Types['RST']

        if not transaction.response.acknowledged:
            rst = self._messageLayer.send_empty(transaction, transaction.response, rst)
            self.send_datagram(rst)
