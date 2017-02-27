import logging
import random
import time
from coapthon.messages.message import Message
from coapthon import defines
from coapthon.messages.request import Request
from coapthon.transaction import Transaction

__author__ = 'Giacomo Tanganelli'

logger = logging.getLogger(__name__)


def str_append_hash(*args):
    """ Convert each argument to a lower case string, appended, then hash """
    ret_hash = ""
    for i in args:
        ret_hash += str(i).lower()

    return hash(ret_hash)


class MessageLayer(object):
    def __init__(self, starting_mid):
        self._transactions = {}
        self._transactions_token = {}
        if starting_mid is not None:
            self._current_mid = starting_mid
        else:
            self._current_mid = random.randint(1, 1000)

    def fetch_mid(self):
        current_mid = self._current_mid
        self._current_mid += 1
        self._current_mid %= 65535
        return current_mid

    def purge(self):
        for k in self._transactions.keys():
            now = time.time()
            transaction = self._transactions[k]
            if transaction.timestamp + defines.EXCHANGE_LIFETIME < now:
                logger.debug("Delete transaction")
                del self._transactions[k]
        for k in self._transactions_token.keys():
            now = time.time()
            transaction = self._transactions_token[k]
            if transaction.timestamp + defines.EXCHANGE_LIFETIME < now:
                logger.debug("Delete transaction")
                del self._transactions_token[k]

    def receive_request(self, request):
        """

        :type request: Request
        :param request: the incoming request
        :rtype : Transaction
        """
        logger.debug("receive_request - " + str(request))
        try:
            host, port = request.source
        except AttributeError:
            return
        key_mid = str_append_hash(host, port, request.mid)
        key_token = str_append_hash(host, port, request.token)

        if key_mid in self._transactions.keys():
            # Duplicated
            self._transactions[key_mid].request.duplicated = True
            transaction = self._transactions[key_mid]
        else:
            request.timestamp = time.time()
            transaction = Transaction(request=request, timestamp=request.timestamp)
            with transaction:
                self._transactions[key_mid] = transaction
                self._transactions_token[key_token] = transaction
        return transaction

    def receive_response(self, response):
        """

        :type response: Response
        :param response:
        :rtype : Transaction
        """
        logger.debug("receive_response - " + str(response))
        try:
            host, port = response.source
        except AttributeError:
            return
        key_mid = str_append_hash(host, port, response.mid)
        key_mid_multicast = str_append_hash(defines.ALL_COAP_NODES, port, response.mid)
        key_token = str_append_hash(host, port, response.token)
        key_token_multicast = str_append_hash(defines.ALL_COAP_NODES, port, response.token)
        if key_mid in self._transactions.keys():
            transaction = self._transactions[key_mid]
            if response.token != transaction.request.token:
                logger.warning("Tokens does not match -  response message " + str(host) + ":" + str(port))
                return None, False
        elif key_token in self._transactions_token:
            transaction = self._transactions_token[key_token]
        elif key_mid_multicast in self._transactions.keys():
            transaction = self._transactions[key_mid_multicast]
        elif key_token_multicast in self._transactions_token:
            transaction = self._transactions_token[key_token_multicast]
            if response.token != transaction.request.token:
                logger.warning("Tokens does not match -  response message " + str(host) + ":" + str(port))
                return None, False
        else:
            logger.warning("Un-Matched incoming response message " + str(host) + ":" + str(port))
            return None, False
        send_ack = False
        if response.type == defines.Types["CON"]:
            send_ack = True

        transaction.request.acknowledged = True
        transaction.completed = True
        transaction.response = response
        if transaction.retransmit_stop is not None:
            transaction.retransmit_stop.set()
        return transaction, send_ack

    def receive_empty(self, message):
        """

        :type message: Message
        :param message:
        :rtype : Transaction
        """
        logger.debug("receive_empty - " + str(message))
        try:
            host, port = message.source
        except AttributeError:
            return
        key_mid = str_append_hash(host, port, message.mid)
        key_mid_multicast = str_append_hash(defines.ALL_COAP_NODES, port, message.mid)
        key_token = str_append_hash(host, port, message.token)
        key_token_multicast = str_append_hash(defines.ALL_COAP_NODES, port, message.token)
        if key_mid in self._transactions.keys():
            transaction = self._transactions[key_mid]
        elif key_token in self._transactions_token:
            transaction = self._transactions_token[key_token]
        elif key_mid_multicast in self._transactions.keys():
            transaction = self._transactions[key_mid_multicast]
        elif key_token_multicast in self._transactions_token:
            transaction = self._transactions_token[key_token_multicast]
        else:
            logger.warning("Un-Matched incoming empty message " + str(host) + ":" + str(port))
            return None

        if message.type == defines.Types["ACK"]:
            if not transaction.request.acknowledged:
                transaction.request.acknowledged = True
            elif not transaction.response.acknowledged:
                transaction.response.acknowledged = True
        elif message.type == defines.Types["RST"]:
            if not transaction.request.acknowledged:
                transaction.request.rejected = True
            elif not transaction.response.acknowledged:
                transaction.response.rejected = True

        if transaction.retransmit_stop is not None:
            transaction.retransmit_stop.set()

        return transaction

    def send_request(self, request):
        """

        :type request: Request
        :param request:
        """
        logger.debug("send_request - " + str(request))
        assert isinstance(request, Request)
        try:
            host, port = request.destination
        except AttributeError:
            return

        request.timestamp = time.time()
        transaction = Transaction(request=request, timestamp=request.timestamp)
        if transaction.request.type is None:
            transaction.request.type = defines.Types["CON"]

        if transaction.request.mid is None:
            transaction.request.mid = self.fetch_mid()

        key_mid = str_append_hash(host, port, request.mid)
        self._transactions[key_mid] = transaction

        key_token = str_append_hash(host, port, request.token)
        self._transactions_token[key_token] = transaction

        return self._transactions[key_mid]

    def send_response(self, transaction):
        """

        :type transaction: Transaction
        :param transaction:
        """
        logger.debug("send_response - " + str(transaction.response))
        if transaction.response.type is None:
            if transaction.request.type == defines.Types["CON"] and not transaction.request.acknowledged:
                transaction.response.type = defines.Types["ACK"]
                transaction.response.mid = transaction.request.mid
                transaction.response.acknowledged = True
                transaction.completed = True
            elif transaction.request.type == defines.Types["NON"]:
                transaction.response.type = defines.Types["NON"]
            else:
                transaction.response.type = defines.Types["CON"]
                transaction.response.token = transaction.request.token

        if transaction.response.mid is None:
            transaction.response.mid = self.fetch_mid()
            try:
                host, port = transaction.response.destination
            except AttributeError:
                return
            key_mid = str_append_hash(host, port, transaction.response.mid)
            self._transactions[key_mid] = transaction

        transaction.request.acknowledged = True
        return transaction

    def send_empty(self, transaction, related, message):
        """

        :param transaction:
        :param related:
        :type message: Message
        :param message:
        """
        logger.debug("send_empty - " + str(message))
        if transaction is None:
            try:
                host, port = message.destination
            except AttributeError:
                return
            key_mid = str_append_hash(host, port, message.mid)
            key_token = str_append_hash(host, port, message.token)
            if key_mid in self._transactions:
                transaction = self._transactions[key_mid]
                related = transaction.response
            elif key_token in self._transactions_token:
                transaction = self._transactions_token[key_token]
                related = transaction.response
            else:
                return message

        if message.type == defines.Types["ACK"]:
            if transaction.request == related:
                transaction.request.acknowledged = True
                transaction.completed = True
                message.mid = transaction.request.mid
                message.code = 0
                message.destination = transaction.request.source
            elif transaction.response == related:
                transaction.response.acknowledged = True
                transaction.completed = True
                message.mid = transaction.response.mid
                message.code = 0
                message.token = transaction.response.token
                message.destination = transaction.response.source

        elif message.type == defines.Types["RST"]:
            if transaction.request == related:
                transaction.request.rejected = True
                message._mid = transaction.request.mid
                message.code = 0
                message.token = transaction.request.token
                message.destination = transaction.request.source
            elif transaction.response == related:
                transaction.response.rejected = True
                transaction.completed = True
                message._mid = transaction.response.mid
                message.code = 0
                message.token = transaction.response.token
                message.destination = transaction.response.source
        return message
