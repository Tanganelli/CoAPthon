import time
from twisted.python import log
from coapthon2 import defines
from coapthon2.messages.message import Message
from coapthon2.messages.response import Response

__author__ = 'giacomo'


class RequestLayer(object):

    def __init__(self, parent):
        self._parent = parent

    def handle_request(self, request):
        host, port = request.source
        key = hash(str(host) + str(port) + str(request.mid))
        if key not in self._parent.received:
            self._parent.received[key] = (request, time.time())
            # TODO Blockwise
            return request
        else:
            request, timestamp = self._parent.received[key]
            request.duplicated = True
            self._parent.received[key] = (request, timestamp)
            response, timestamp = self._parent.sent.get(key)
            if isinstance(response, Response):
                return response
            elif request.acknowledged:
                ack = Message.new_ack(request)
                return ack
            elif request.rejected:
                rst = Message.new_rst(request)
                return rst
            else:
                # The server has not yet decided, whether to acknowledge or
                # reject the request. We know for sure that the server has
                # received the request though and can drop this duplicate here.
                return None

    def process(self, request):
        method = defines.codes[request.code]
        if method == 'GET':
            response = self.handle_get(request)
        elif method == 'POST':
            response = self.handle_post(request)
        elif method == 'PUT':
            response = self.handle_put(request)
        elif method == 'DELETE':
            response = self.handle_delete(request)
        else:
            response = None
        return response

    def handle_put(self, request):
        path = request.uri_path
        path = path.strip("/")
        node = self._parent.root.find_complete(path)
        if node is not None:
            resource = node.value
        else:
            resource = None
        response = Response()
        response.destination = request.source
        if resource is None:
            # Create request
            # response = self._parent.create_resource(path, request, response)
            # log.msg(self._parent.root.dump())
            #
            response = self._parent.send_error(request, response, 'METHOD_NOT_ALLOWED')
            return response
        else:
            # Update request
            response = self._parent.update_resource(path, request, response, resource)
            return response

    def handle_post(self, request):
        path = request.uri_path
        path = path.strip("/")
        node = self._parent.root.find_complete(path)
        if node is not None:
            resource = node.value
        else:
            resource = None
        response = Response()
        response.destination = request.source
        if resource is None:
            # Create request
            response = self._parent.create_resource(path, request, response, "render_POST")
            log.msg(self._parent.root.dump())
            return response
        else:
            # Update request
            response = self._parent.update_resource(path, request, response, resource, "render_POST")
            return response

    def handle_delete(self, request):
        path = request.uri_path
        path = path.strip("/")
        node = self._parent.root.find_complete(path)
        if node is not None:
            resource = node.value
        else:
            resource = None
        response = Response()
        response.destination = request.source
        if resource is None:
            # Create request
            response = self._parent.send_error(request, response, 'NOT_FOUND')
            log.msg("Resource Not Found")
            return response
        else:
            # Delete
            response = self._parent.delete_resource(request, response, node)
            return response

    def handle_get(self, request):
        path = request.uri_path
        response = Response()
        response.destination = request.source
        if path == defines.DISCOVERY_URL:
            response = self._parent.discover(request, response)
        else:
            path = path.strip("/")
            node = self._parent.root.find_complete(path)
            if node is not None:
                resource = node.value
            else:
                resource = None
            if resource is None:
                # Not Found
                response = self._parent.send_error(request, response, 'NOT_FOUND')
            else:
                response = self._parent.get_resource(request, response, resource)
        return response