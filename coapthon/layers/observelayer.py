import logging
import time
from coapthon import defines

__author__ = 'Giacomo Tanganelli'

logger = logging.getLogger(__name__)


class ObserveItem(object):
    def __init__(self, timestamp, non_counter, allowed, transaction):
        """
        Data structure for the Observe option

        :param timestamp: the timestamop of last message sent
        :param non_counter: the number of NON notification sent
        :param allowed: if the client is allowed as observer
        :param transaction: the transaction
        """
        self.timestamp = timestamp
        self.non_counter = non_counter
        self.allowed = allowed
        self.transaction = transaction


class ObserveLayer(object):
    """
    Manage the observing feature. It store observing relationships.
    """
    def __init__(self):
        self._relations = {}

    def send_request(self, request):
        """
        Add itself to the observing list

        :param request: the request
        :return: the request unmodified
        """
        if request.observe == 0:
            # Observe request
            host, port = request.destination
            key_token = hash(str(host) + str(port) + str(request.token))

            self._relations[key_token] = ObserveItem(time.time(), None, True, None)

        return request

    def receive_response(self, transaction):
        """
        Sets notification's parameters.

        :type transaction: Transaction
        :param transaction: the transaction
        :rtype : Transaction
        :return: the modified transaction
        """
        host, port = transaction.response.source
        key_token = hash(str(host) + str(port) + str(transaction.response.token))
        if key_token in self._relations and transaction.response.type == defines.Types["CON"]:
            transaction.notification = True
        return transaction

    def send_empty(self, message):
        """
        Eventually remove from the observer list in case of a RST message.

        :type message: Message
        :param message: the message
        :return: the message unmodified
        """
        host, port = message.destination
        key_token = hash(str(host) + str(port) + str(message.token))
        if key_token in self._relations and message.type == defines.Types["RST"]:
            del self._relations[key_token]
        return message

    def receive_request(self, transaction):
        """
        Manage the observe option in the request end eventually initialize the client for adding to
        the list of observers or remove from the list.

        :type transaction: Transaction
        :param transaction: the transaction that owns the request
        :rtype : Transaction
        :return: the modified transaction
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
        elif transaction.request.observe == 1:
            host, port = transaction.request.source
            key_token = hash(str(host) + str(port) + str(transaction.request.token))
            logger.info("Remove Subscriber")
            try:
                del self._relations[key_token]
            except KeyError:
                pass

        return transaction

    def receive_empty(self, empty, transaction):
        """
        Manage the observe feature to remove a client in case of a RST message receveide in reply to a notification.

        :type empty: Message
        :param empty: the received message
        :type transaction: Transaction
        :param transaction: the transaction that owns the notification message
        :rtype : Transaction
        :return: the modified transaction
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
        Finalize to add the client to the list of observer.

        :type transaction: Transaction
        :param transaction: the transaction that owns the response
        :return: the transaction unmodified
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
        """
        Prepare notification for the resource to all interested observers.

        :rtype: list
        :param resource: the resource for which send a new notification
        :param root: deprecated
        :return: the list of transactions to be notified
        """
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
        """
        Remove a subscriber based on token.

        :param message: the message
        """
        logger.debug("Remove Subcriber")
        host, port = message.destination
        key_token = hash(str(host) + str(port) + str(message.token))
        try:
            self._relations[key_token].transaction.completed = True
            del self._relations[key_token]
        except KeyError:
            logger.warning("No Subscriber")

