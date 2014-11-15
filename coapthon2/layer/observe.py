import time
from twisted.python import log
from coapthon2 import defines
from coapthon2.messages.option import Option
from coapthon2.messages.request import Request
from coapthon2.messages.response import Response
from coapthon2.serializer import Serializer
from coapthon2.utils import Tree

__author__ = 'Giacomo Tanganelli'
__version__ = "2.0"


class ObserveLayer(object):
    """
    Handles the Observing feature.
    """
    def __init__(self, parent):
        """
        Initialize a Observe Layer.

        :type parent: coapserver.CoAP
        :param parent: the CoAP server
        """
        self._parent = parent

    def notify_deletion(self, node):
        """
        Finds the observers that must be notified about the cancellation of the observed resource.

        :type node: coapthon2.utils.Tree
        :param node: the node which has the deleted resource
        :return: the list of commands that must be executed to notify clients
        """
        assert isinstance(node, Tree)
        resource = node.value
        observers = self._parent.relation.get(resource)
        if observers is None:
            resource.observe_count += 1
            return
        now = int(round(time.time() * 1000))
        commands = []
        for item in observers.keys():
            old, host, port, token = observers[item]
            #send notification
            commands.append((self._parent.prepare_notification, [(resource, host, port, token)], {}))
            observers[item] = (now, host, port, token)
        resource.observe_count += 1
        self._parent.relation[resource] = observers
        return commands

    def notify(self, node):
        """
        Finds the observers that must be notified about the update of the observed resource.

        :type node: coapthon2.utils.Tree
        :param node: the node which has the deleted resource
        :return: the list of commands that must be executed to notify clients
        """
        assert isinstance(node, Tree)
        resource = node.value
        observers = self._parent.relation.get(resource)
        if observers is None:
            resource.observe_count += 1
            return
        now = int(round(time.time() * 1000))
        commands = []
        for item in observers.keys():
            old, host, port, token = observers[item]
            #send notification
            commands.append((self._parent.prepare_notification, [(resource, host, port, token)], {}))
            observers[item] = (now, host, port, token)
        resource.observe_count += 1
        self._parent.relation[resource] = observers
        return commands

    def prepare_notification(self, t):
        """
        Create the notification message.


        :type t: (resource, host, port, token)
        :param t: the arguments of the notification message
        :return: the notification message
        """
        resource, host, port, token = t
        response = Response()
        response.destination = (host, port)
        response.token = token

        option = Option()
        option.number = defines.inv_options['Observe']
        option.value = resource.observe_count
        response.add_option(option)
        method = getattr(resource, 'render_GET', None)
        if hasattr(method, '__call__'):
            # Render_GET
            response.code = defines.responses['CONTENT']
            try:
                response.payload = method(notification=True)
            except TypeError:
                response.payload = method()
            #TODO Blockwise
            #Reliability
            request = Request()
            request.type = defines.inv_types['CON']
            request.acknowledged = True
            response = self._parent.reliability_response(request, response)
            #Matcher
            response = self._parent.matcher_response(response)
            return response, resource
        else:
            response.code = defines.responses['METHOD_NOT_ALLOWED']
            #TODO Blockwise
            #Reliability
            request = Request()
            request.type = defines.inv_types['CON']
            request.acknowledged = True
            response = self._parent.reliability_response(request, response)
            #Matcher
            response = self._parent.matcher_response(response)
            return response, resource

    def prepare_notification_deletion(self, t):
        """
        Create the notification message for deleted resource.


        :type t: (resource, host, port, token)
        :param t: the arguments of the notification message
        :return: the notification message
        """
        resource, host, port, token = t
        response = Response()
        response.destination = (host, port)
        response.token = token
        option = Option()
        option.number = defines.inv_options['Observe']
        option.value = resource.observe_count
        response.add_option(option)
        response.code = defines.responses['DELETED']
        response.payload = None
        #TODO Blockwise
        #Reliability
        request = Request()
        request.type = defines.inv_types['CON']
        request.acknowledged = True
        response = self._parent.reliability_response(request, response)
        #Matcher
        response = self._parent.matcher_response(response)
        return response, resource

    def send_notification(self, t):
        """
        Sends a notification message.

        :param t: (the notification message, the resource)
        """
        assert isinstance(t, tuple)
        notification_message, resource = t
        host, port = notification_message.destination
        serializer = Serializer()
        self._parent.schedule_retrasmission(t)
        print "Notification Message send to " + host + ":" + str(port)
        print "----------------------------------------"
        print notification_message
        print "----------------------------------------"
        notification_message = serializer.serialize(notification_message)
        self._parent.transport.write(notification_message, (host, port))

    def add_observing(self, resource, response):
        """
        Add an observer to a resource and sets the Observe option in the response.

        :param resource: the resource of interest
        :param response: the response
        :return: response
        """
        host, port = response.destination
        key = hash(str(host) + str(port) + str(response.token))
        observers = self._parent.relation.get(resource)
        now = int(round(time.time() * 1000))
        observe_count = resource.observe_count
        if observers is None:
            log.msg("Initiate an observe relation between " + str(host) + ":" +
                    str(port) + " and resource " + str(resource.path))
            observers = {key: (now, host, port, response.token)}
        elif key not in observers:
            log.msg("Initiate an observe relation between " + str(host) + ":" +
                    str(port) + " and resource " + str(resource.path))
            observers[key] = (now, host, port, response.token)
        else:
            log.msg("Update observe relation between " + str(host) + ":" +
                    str(port) + " and resource " + str(resource.path))
            old, host, port, token = observers[key]
            observers[key] = (now, host, port, token)
        self._parent.relation[resource] = observers
        option = Option()
        option.number = defines.inv_options['Observe']
        option.value = observe_count
        response.add_option(option)
        return response

    def remove_observers(self, node):
        """
        Remove all the observers of a resource and notifies the delete of the resource observed.

        :type node: coapthon2.utils.Tree
        :param node: the node which has the deleted resource
        :return: the list of commands that must be executed to notify clients
        """
        assert isinstance(node, Tree)
        commands = []
        log.msg("Remove observers")
        for n in node.children:
            assert isinstance(n, Tree)
            if len(n.children) > 0:
                c = self.remove_observers(n)
                commands += c
            resource = n.value
            observers = self._parent.relation.get(resource)
            if observers is not None:
                for item in observers.keys():
                    old, host, port, token = observers[item]
                    #send notification
                    commands.append((self._parent.prepare_notification, [(resource, host, port, token),
                                                                         defines.responses['DELETED']], {}))
                    del observers[item]
                resource.observe_count += 1
            del self._parent.relation[resource]
        return commands

    def update_relations(self, node, resource):
        """
        Update a relation. It is used when a resource change due a POST request, without changing its path.

        :type node: coapthon2.utils.Tree
        :param node: the node which has the deleted resource
        :param resource: the new resource
        """
        old_resource = node.value
        observers = self._parent.relation.get(old_resource)
        if observers is not None:
            del self._parent.relation[old_resource]
            self._parent.relation[resource] = observers

    def remove_observer(self, response, resource):
        """
        Remove an observer for a certain resource.

        :param response: the response message which has not been acknowledge
        :param resource: the resource
        """
        log.msg("Remove observer for the resource")
        host, port = response.destination
        key = hash(str(host) + str(port) + str(response.token))
        observers = self._parent.relation.get(resource)
        if observers is not None and key in observers.keys():
            del observers[key]
            self._parent.relation[resource] = observers