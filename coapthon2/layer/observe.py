import time
from twisted.python import log
from coapthon2 import defines
from coapthon2.messages.option import Option
from coapthon2.messages.request import Request
from coapthon2.messages.response import Response
from coapthon2.serializer import Serializer
from coapthon2.utils import Tree

__author__ = 'giacomo'


class ObserveLayer(object):
    def __init__(self, parent):
        self._parent = parent

    def notify(self, node):
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

    def prepare_notification(self, t, code=None):
        resource, host, port, token = t
        response = Response()
        response.destination = (host, port)
        response.token = token
        if code is None:
            option = Option()
            option.number = defines.inv_options['Observe']
            option.value = resource.observe_count
            response.add_option(option)
            method = getattr(resource, 'render_GET', None)
            if hasattr(method, '__call__'):
                # Render_GET
                response.code = defines.responses['CONTENT']
                response.payload = method()
                #TODO Blockwise
                #Reliability
                request = Request()
                request.type = defines.inv_types['CON']
                request.acknowledged = True
                response = self._parent.reliability_response(request, response)
                #Matcher
                response = self._parent.matcher_response(response)
                return response, host, port
            else:
                response.code = code
                #TODO Blockwise
                #Reliability
                request = Request()
                request.type = defines.inv_types['CON']
                request.acknowledged = True
                response = self._parent.reliability_response(request, response)
                #Matcher
                response = self._parent.matcher_response(response)
                return response, host, port
        return None

    def send_notification(self, t):
        response, host, port = t
        serializer = Serializer()
        self._parent.schedule_retrasmission(t)
        response = serializer.serialize(response)
        self._parent.transport.write(response, (host, port))

    def add_observing(self, resource, response):
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
        resource.observe_count += 1
        return response, resource

    def remove_observers(self, node):
        assert isinstance(node, Tree)
        commands = []
        log.msg("Remove observers for " + node.find_path())
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