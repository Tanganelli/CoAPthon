import logging
import time
import threading
from coapthon import defines

__author__ = 'Giacomo Tanganelli'

logger = logging.getLogger(__name__)


class ObserveItem(object):
    def __init__(self, timestamp, non_counter, allowed, transaction, serv=None):
        """
        Data structure for the Observe option

        :param timestamp: the timestamop of last message sent
        :param non_counter: the number of NON notification sent
        :param allowed: if the client is allowed as observer
        :param transaction: the transaction
        :param serv: reference to CoAP object
        """
        self.timestamp = timestamp
        self.non_counter = non_counter
        self.allowed = allowed
        self.transaction = transaction

        # parameters for dynamic resource observing
        self.conditional = False
        self.conditions = {}
        self.last_notify = time.time()
        self.timer = None
        self.coap = serv

    # timer for notification procedure is set at (pmax - pmin)/2
    def pmax_timer(self):
        self.coap.notify(self.transaction.resource)

    def start_timer(self):
        pmin = 0
        pmax = 0
        for cond in self.conditions:
            if cond == "pmin":
                pmin = self.conditions[cond]
            elif cond == "pmax":
                pmax = self.conditions[cond]
        if pmax == 0:
            return
        else:
            self.timer = threading.Timer((pmax-pmin)/2, self.pmax_timer)
            self.timer.start()


class ObserveLayer(object):
    """
    Manage the observing feature. It store observing relationships.
    """
    def __init__(self, server=None):
        self._relations = {}
        self._server = server

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
        if request.observe == 1:
            # Cancelling observe explicitly
            self.remove_subscriber(request)

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
            self._relations[key_token] = ObserveItem(time.time(), non_counter, allowed, transaction, self._server)

            # check if the observing request has dynamic parameters (sent inside uri_query field)
            if transaction.request.uri_query is not None:
                logger.info("Dynamic Observing registration")
                self._relations[key_token].conditional = True
                self._relations[key_token].conditions = ObserveLayer.parse_uri_query(transaction.request.uri_query)
                self._relations[key_token].start_timer()

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
                # checking dynamic resource parameters
                if self._relations[key].conditional:
                    if self.verify_conditions(self._relations[key]) is False:
                        continue
                    # updating relation timestamp and resetting timer
                    self._relations[key].last_notify = time.time()
                    self._relations[key].timer.cancel()
                    self._relations[key].start_timer()

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
        logger.debug("Remove Subscriber")
        host, port = message.destination
        key_token = hash(str(host) + str(port) + str(message.token))
        try:
            self._relations[key_token].transaction.completed = True
            del self._relations[key_token]
        except AttributeError:
            logger.warning("No Transaction")
        except KeyError:
            logger.warning("No Subscriber")

    @staticmethod
    def parse_uri_query(uri_query):
        """
        parse the conditional parameters for the conditional observing

        :return: a map with pairs [parameter, value]
        """
        dict_att = {}
        print(uri_query)
        attributes = uri_query.split(";")
        for att in attributes:
            a = att.split("=")
            if len(a) > 1:
                if str(a[0]) == "band":
                    a[1] = bool(a[1])
                if a[1].isdigit():
                    a[1] = int(a[1])
                dict_att[str(a[0])] = a[1]
            else:
                dict_att[str(a[0])] = a[0]
        print (dict_att)
        return dict_att

    @staticmethod
    def verify_conditions(item):
        """
        checks if the changed resource requires a notification

        :param item: ObserveItem
        :return: Boolean
        """
        for cond in item.conditions:
            if cond == "pmin":
                # CURRENT TIME - TIMESTAMP < PMIN
                t = int(time.time() - item.last_notify)
                if t < int(item.conditions[cond]):
                    return False
        return True

