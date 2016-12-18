import logging
import time
from coapthon import defines

__author__ = 'Giacomo Tanganelli'

logger = logging.getLogger(__name__)


class ObserveItem(object):
    def __init__(self, timestamp, non_counter, allowed, transaction):
        self.timestamp = timestamp
        self.non_counter = non_counter
        self.allowed = allowed
        self.transaction = transaction


class ObserveLayer(object):
    def __init__(self):
        self._relations = {}

    def send_request(self, request):
        """

        :param request:
        """
        if request.observe == 0:
            # Observe request
            host, port = request.destination
            key_token = hash(str(host) + str(port) + str(request.token))

            self._relations[key_token] = ObserveItem(time.time(), None, True, None)

        return request

    def receive_response(self, transaction):
        """

        :type transaction: Transaction
        :param transaction:
        :rtype : Transaction
        """
        host, port = transaction.response.source
        key_token = hash(str(host) + str(port) + str(transaction.response.token))
        if key_token in self._relations and transaction.response.type == defines.Types["CON"]:
            transaction.notification = True
        return transaction

    def send_empty(self, message):
        """

        :type message: Message
        :param message:
        """
        host, port = message.destination
        key_token = hash(str(host) + str(port) + str(message.token))
        if key_token in self._relations and message.type == defines.Types["RST"]:
            del self._relations[key_token]
        return message

    def receive_request(self, transaction):
        """

        :type transaction: Transaction
        :param transaction:
        :rtype : Transaction
        """
        if transaction.request.observe == 0:
            # Observe request
            host, port = transaction.request.source
            key_token = hash(str(host) + str(port) + str(transaction.request.token))
            non_counter = 0
            if key_token in self._relations:
                # Renew registration
                allowed = True
            else:
                allowed = False
            self._relations[key_token] = ObserveItem(time.time(), non_counter, allowed, transaction)

        return transaction

    def receive_empty(self, empty, transaction):
        """

        :type empty: Message
        :param empty:
        :type transaction: Transaction
        :param transaction:
        :rtype : Transaction
        """
        if empty.type == defines.Types["RST"]:
            host, port = transaction.request.source
            key_token = hash(str(host) + str(port) + str(transaction.request.token))
            logger.info("Remove Subscriber")
            try:
                del self._relations[key_token]
            except KeyError:
                pass
            transaction.completed = True
        return transaction

    def send_response(self, transaction):
        """

        :type transaction: Transaction
        :param transaction:
        """
        host, port = transaction.request.source
        key_token = hash(str(host) + str(port) + str(transaction.request.token))
        if key_token in self._relations:
            if transaction.response.code == defines.Codes.CONTENT.number:
                if transaction.resource is not None and transaction.resource.observable:

                    transaction.response.observe = transaction.resource.observe_count
                    self._relations[key_token].allowed = True
                    self._relations[key_token].transaction = transaction
                    self._relations[key_token].timestamp = time.time()
                else:
                    del self._relations[key_token]
            elif transaction.response.code >= defines.Codes.ERROR_LOWER_BOUND:
                del self._relations[key_token]
        return transaction

    def notify(self, resource, root=None):
        ret = []
        if root is not None:
            resource_list = root.with_prefix_resource(resource.path)
        else:
            resource_list = [resource]
        for key in self._relations.keys():
            if self._relations[key].transaction.resource in resource_list:
                if self._relations[key].non_counter > defines.MAX_NON_NOTIFICATIONS \
                        or self._relations[key].transaction.request.type == defines.Types["CON"]:
                    self._relations[key].transaction.response.type = defines.Types["CON"]
                    self._relations[key].non_counter = 0
                elif self._relations[key].transaction.request.type == defines.Types["NON"]:
                    self._relations[key].non_counter += 1
                    self._relations[key].transaction.response.type = defines.Types["NON"]
                self._relations[key].transaction.resource = resource
                del self._relations[key].transaction.response.mid
                del self._relations[key].transaction.response.token
                ret.append(self._relations[key].transaction)
        return ret

    def remove_subscriber(self, message):
        logger.debug("Remove Subcriber")
        host, port = message.destination
        key_token = hash(str(host) + str(port) + str(message.token))
        try:
            self._relations[key_token].transaction.completed = True
            del self._relations[key_token]
        except KeyError:
            logger.warning("No Subscriber")

