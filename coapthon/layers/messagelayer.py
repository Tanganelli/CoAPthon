import logging
import time
from coapthon.messages.message import Message
from coapthon import defines
from coapthon.transaction import Transaction

logger = logging.getLogger(__name__)


class MessageLayer(object):
    def __init__(self, starting_mid):
        self._transactions = {}
        if starting_mid is not None:
            self._current_mid = starting_mid
        else:
            self._current_mid = 1

    def purge(self):
        for k in self._transactions.keys():
            now = time.time()
            transaction = self._transactions[k]
            if transaction.timestamp + defines.EXCHANGE_LIFETIME < now:
                logger.debug("Delete transaction")
                del self._transactions[k]

    def receive_request(self, request):
        """

        :type request: Request
        :param request:
        :rtype : Transaction
        """

        try:
            host, port = request.source
        except AttributeError:
            return
        key_mid = hash(str(host) + str(port) + str(request.mid))
        if key_mid in self._transactions.keys():
            # Duplicated
            self._transactions[key_mid].request.duplicated = True
        else:
            request.timestamp = time.time()
            transaction = Transaction(request=request, timestamp=request.timestamp)
            self._transactions[key_mid] = transaction

        return self._transactions[key_mid]

    def receive_response(self, response):
        """

        :type response: Response
        :param response:
        :rtype : Transaction
        """
        try:
            host, port = response.source
        except AttributeError:
            return
        key_mid = hash(str(host) + str(port) + str(response.mid))
        if key_mid in self._transactions.keys():
            self._transactions[key_mid].request.acknowledged = True
            self._transactions[key_mid].completed = True
            if self._transactions[key_mid].retransmit_stop is not None:
                self._transactions[key_mid].retransmit_stop.set()
        else:
            logger.warning("Un-Matched incoming response message " + str(host) + ":" + str(port))
            return None
        return self._transactions[key_mid]

    def receive_empty(self, message):
        """

        :type message: Message
        :param message:
        :rtype : Transaction
        """

        try:
            host, port = message.source
        except AttributeError:
            return
        key_mid = hash(str(host) + str(port) + str(message.mid))
        if key_mid in self._transactions.keys():
            if message.type == defines.Types["ACK"]:
                if not self._transactions[key_mid].request.acknowledged:
                    self._transactions[key_mid].request.acknowledged = True
                elif not self._transactions[key_mid].response.acknowledged:
                    self._transactions[key_mid].response.acknowledged = True
            elif message.type == defines.Types["RST"]:
                if not self._transactions[key_mid].request.acknowledged:
                    self._transactions[key_mid].request.rejected = True
                elif not self._transactions[key_mid].response.acknowledged:
                    self._transactions[key_mid].response.rejected = True

            if self._transactions[key_mid].retransmit_stop is not None:
                self._transactions[key_mid].retransmit_stop.set()
        else:
            logger.warning("Un-Matched incoming empty message " + str(host) + ":" + str(port))
            return None

        return self._transactions[key_mid]

    def send_request(self, request):
        """

        :type transaction: Transaction
        :param transaction:
        :type request: Request
        :param request:
        """
        try:
            host, port = request.source
        except AttributeError:
            return
        key_mid = hash(str(host) + str(port) + str(request.mid))
        request.timestamp = time.time()
        transaction = Transaction(request=request, timestamp=request.timestamp)
        if transaction.request.type is None:
            transaction.request.type = defines.Types["CON"]

        if transaction.request.mid is None:
            transaction.request.mid = self._current_mid
            self._current_mid += 1 % 65535

        self._transactions[key_mid] = transaction

        return self._transactions[key_mid]

    def send_response(self, transaction):
        """

        :type transaction: Transaction
        :param transaction:
        """

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

        if transaction.response.mid is None:
            transaction.response.mid = self._current_mid
            self._current_mid += 1 % 65535
            try:
                host, port = transaction.response.destination
            except AttributeError:
                return
            key_mid = hash(str(host) + str(port) + str(transaction.response.mid))
            self._transactions[key_mid] = transaction

        transaction.request.acknowledged = True
        return transaction

    def send_empty(self, transaction, related, message):
        """

        :type transaction: Transaction
        :param transaction:
        :type message: Message
        :param message:
        """
        if message.type == defines.Types["ACK"]:
            if transaction.request == related:
                transaction.request.acknowledged = True
                message._mid = transaction.request.mid
                message.code = 0
                message.token = transaction.request.token
                message.destination = transaction.request.source
            elif transaction.response == related:
                transaction.response.acknowledged = True
                transaction.completed = True
                message._mid = transaction.response.mid
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

