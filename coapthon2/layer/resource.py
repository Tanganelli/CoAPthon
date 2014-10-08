from threading import Timer
from coapthon2 import defines
from coapthon2.messages.message import Message
from coapthon2.resources.resource import Resource
from coapthon2.utils import Tree

__author__ = 'Giacomo Tanganelli'
__version__ = "2.0"


class ResourceLayer(object):
    """
    Handles the Resources.
    """
    def __init__(self, parent):
        """
        Initialize a Resource Layer.

        :type parent: coapserver.CoAP
        :param parent: the CoAP server
        """
        self._parent = parent

    def edit_resorce(self, request, response, node, lp, p):
        """
        Render a POST on an already created resource.

        :type node: coapthon2.utils.Tree
        :param request: the request
        :param response: the response
        :param node: the node which has the resource
        :param lp: the location_path attribute of the resource
        :param p: the local path of the resource (only the last section of the split path)
        :return: the response
        """
        method = getattr(node.value, "render_POST", None)
        if hasattr(method, '__call__'):
            t = Timer(defines.SEPARATE_TIMEOUT, self.send_ack, [request])
            t.start()
            new_payload = method(request=request, payload=request.payload, query=request.query)
            t.cancel()
            if isinstance(new_payload, dict):
                etag = new_payload.get("ETag")
                location_query = new_payload.get("Location-Query")
                resource = new_payload.get("Resource")
                separate = new_payload.get("Separate")
                callback = new_payload.get("Callback")
                new_payload = new_payload.get("Payload")
            else:
                etag = None
                location_query = request.query
                resource = None
                separate = None
                callback = None

            if separate is not None:
                # Handle separate
                ack = Message.new_ack(request)
                ack.mid = self._parent.current_mid % (1 << 16)
                self._parent.current_mid += 1
                host, port = request.source
                self._parent.send(ack, host, port)
                request.acknowledged = True
                new_payload = callback(request=request, payload=request.payload, query=request.query)
                if isinstance(new_payload, dict):
                    etag = new_payload.get("ETag")
                    location_query = new_payload.get("Location-Query")
                    resource = new_payload.get("Resource")
                    new_payload = new_payload.get("Payload")
                else:
                    etag = None
                    location_query = request.query
                    resource = None

            if new_payload is not None and new_payload != -1:
                if resource is None:
                    origin = node.value
                    assert isinstance(origin, Resource)
                    origin_class = origin.__class__
                    resource = origin_class(origin)
                elif not isinstance(resource, Resource):
                    return self._parent.send_error(request, response, 'INTERNAL_SERVER_ERROR')

                if request.content_type is not None and request.content_type in defines.content_types:
                    resource.raw_payload[request.content_type] = new_payload
                else:
                    resource.raw_payload[defines.inv_content_types["text/plain"]] = new_payload

                resource.path = p
                resource.observe_count = node.value.observe_count
                # Observe
                self._parent.update_relations(node, resource)
                node.value = resource
                # Observe
                self._parent.notify(node)
                if etag is not None:
                    resource.etag = etag
                    response.etag = resource.etag
                response.location_path = lp

                if location_query is not None and len(location_query) > 0 and location_query != "?":
                    if isinstance(location_query, str):
                        location_query = location_query.strip("?")
                        lq = location_query.split("&")
                    else:
                        lq = location_query
                    response.location_query = lq

                response.code = defines.responses['CREATED']

                response.payload = None
                # Token
                response.token = request.token
                #TODO Blockwise
                #Reliability
                response = self._parent.reliability_response(request, response)
                #Matcher
                response = self._parent.matcher_response(response)
                return response
            elif new_payload == -1:
                return self._parent.send_error(request, response, 'METHOD_NOT_ALLOWED')
            else:
                return self._parent.send_error(request, response, 'INTERNAL_SERVER_ERROR')
        else:
            return self._parent.send_error(request, response, 'METHOD_NOT_ALLOWED')

    def add_resorce(self, request, response, old, lp, p):
        """
        Render a POST on aa new resource.

        :type old: coapthon2.utils.Tree
        :param request: the request
        :param response: the response
        :param old: the node which has the parent of the resource
        :param lp: the location_path attribute of the resource
        :param p: the local path of the resource (only the last section of the split path)
        :return: the response
        """
        method = getattr(old.value, "render_POST", None)
        if hasattr(method, '__call__'):
            t = Timer(defines.SEPARATE_TIMEOUT, self.send_ack, [request])
            t.start()
            new_payload = method(request=request, payload=request.payload, query=request.query)
            t.cancel()
            if isinstance(new_payload, dict):
                etag = new_payload.get("ETag")
                location_query = new_payload.get("Location-Query")
                resource = new_payload.get("Resource")
                separate = new_payload.get("Separate")
                callback = new_payload.get("Callback")
                new_payload = new_payload.get("Payload")
            else:
                etag = None
                location_query = request.query
                resource = None
                separate = None
                callback = None

            if separate is not None:
                # Handle separate
                ack = Message.new_ack(request)
                ack.mid = self._parent.current_mid % (1 << 16)
                self._parent.current_mid += 1
                host, port = request.source
                self._parent.send(ack, host, port)
                request.acknowledged = True
                new_payload = callback(request=request, payload=request.payload, query=request.query)
                if isinstance(new_payload, dict):
                    etag = new_payload.get("ETag")
                    location_query = new_payload.get("Location-Query")
                    resource = new_payload.get("Resource")
                    new_payload = new_payload.get("Payload")
                else:
                    etag = None
                    location_query = request.query
                    resource = None

            if new_payload is not None and new_payload != -1:
                if resource is None:
                    origin = old.value
                    assert isinstance(origin, Resource)
                    origin_class = origin.__class__
                    resource = origin_class(origin)
                elif not isinstance(resource, Resource):
                    return self._parent.send_error(request, response, 'INTERNAL_SERVER_ERROR')

                if request.content_type is not None and request.content_type in defines.content_types:
                    resource.raw_payload[request.content_type] = new_payload
                else:
                    resource.raw_payload[defines.inv_content_types["text/plain"]] = new_payload

                resource.path = p
                node = old.add_child(resource)
                # Observe
                self._parent.notify(node)
                if etag is not None:
                    resource.etag = etag
                    response.etag = resource.etag
                response.location_path = lp

                if location_query is not None and len(location_query) > 0 and location_query != "?":
                    if isinstance(location_query, str):
                        location_query = location_query.strip("?")
                        lq = location_query.split("&")
                    else:
                        lq = location_query
                    response.location_query = lq

                response.code = defines.responses['CREATED']

                response.payload = None
                # Token
                response.token = request.token
                #TODO Blockwise
                #Reliability
                response = self._parent.reliability_response(request, response)
                #Matcher
                response = self._parent.matcher_response(response)
                return response
            elif new_payload == -1:
                return self._parent.send_error(request, response, 'METHOD_NOT_ALLOWED')
            else:
                return self._parent.send_error(request, response, 'INTERNAL_SERVER_ERROR')
        else:
            return self._parent.send_error(request, response, 'METHOD_NOT_ALLOWED')

    def create_resource(self, path, request, response):
        """
        Render a POST request.

        :param path: the path of the request
        :param request: the request
        :param response: the response
        :return: the response
        """
        paths = path.split("/")
        last, p = self._parent.root.find_complete_last(paths)
        if p is None:
            # Resource already present
            return self.edit_resorce(request, response, last, path, paths[-1])
        else:
            lp = last.find_path() + p
            if last.value.allow_children:
                    return self.add_resorce(request, response, last, lp[1:], p)
            else:
                return self._parent.send_error(request, response, 'METHOD_NOT_ALLOWED')

    def update_resource(self, request, response, node):
        """
        Render a PUT request.

        :type node: coapthon2.utils.Tree
        :param request: the request
        :param response: the response
        :param node: the node which has the resource
        :return: the response
        """
        resource = node.value
        # If-Match
        if request.has_if_match:
            if None not in request.if_match and str(resource.etag) not in request.if_match:
                return self._parent.send_error(request, response, 'PRECONDITION_FAILED')
        # If-None-Match
        if request.has_if_none_match:
            return self._parent.send_error(request, response, 'PRECONDITION_FAILED')
        method = getattr(resource, "render_PUT", None)
        if hasattr(method, '__call__'):
            t = Timer(defines.SEPARATE_TIMEOUT, self.send_ack, [request])
            t.start()
            new_payload = method(request=request, payload=request.payload, query=request.query)
            t.cancel()
            if isinstance(new_payload, dict):
                etag = new_payload.get("ETag")
                separate = new_payload.get("Separate")
                callback = new_payload.get("Callback")
                new_payload = new_payload.get("Payload")
            else:
                etag = None
                separate = None
                callback = None
            if separate is not None:
                # Handle separate
                ack = Message.new_ack(request)
                ack.mid = self._parent.current_mid % (1 << 16)
                self._parent.current_mid += 1
                host, port = request.source
                self._parent.send(ack, host, port)
                request.acknowledged = True
                new_payload = callback(request=request, payload=request.payload, query=request.query)
                if isinstance(new_payload, dict):
                    etag = new_payload.get("ETag")
                    new_payload = new_payload.get("Payload")
                else:
                    etag = None

            if new_payload is not None and new_payload != -1:
                if etag is not None:
                    resource.etag = etag
                    response.etag = resource.etag
                if isinstance(node.value.raw_payload, dict):
                    if request.content_type is not None and request.content_type in defines.content_types:
                        node.value.raw_payload[request.content_type] = new_payload
                    else:
                        node.value.raw_payload[defines.inv_content_types["text/plain"]] = new_payload
                else:
                    node.value.payload = new_payload

                # Observe
                self._parent.notify(node)

                response.code = defines.responses['CHANGED']
                response.payload = None
                # Token
                response.token = request.token
                #TODO Blockwise
                #Reliability
                response = self._parent.reliability_response(request, response)
                #Matcher
                response = self._parent.matcher_response(response)
                return response
            elif new_payload == -1:
                return self._parent.send_error(request, response, 'METHOD_NOT_ALLOWED')
            else:
                return self._parent.send_error(request, response, 'INTERNAL_SERVER_ERROR')
        else:
            return self._parent.send_error(request, response, 'METHOD_NOT_ALLOWED')

    def delete_resource(self, request, response, node):
        """
        Render a DELETE request.

        :type node: coapthon2.utils.Tree
        :param request: the request
        :param response: the response
        :param node: the node which has the resource
        :return: the response
        """
        assert isinstance(node, Tree)
        method = getattr(node.value, 'render_DELETE', None)
        if hasattr(method, '__call__'):
            t = Timer(defines.SEPARATE_TIMEOUT, self.send_ack, [request])
            t.start()
            ret = method(request=request, query=request.query)
            t.cancel()
            if ret != -1:
                parent = node.parent
                assert isinstance(parent, Tree)
                # Observe
                self._parent.notify_deletion(node)
                self._parent.remove_observers(node)

                parent.del_child(node)
                response.code = defines.responses['DELETED']
                response.payload = None
                # Token
                response.token = request.token
                #TODO Blockwise
                #Reliability
                response = self._parent.reliability_response(request, response)
                #Matcher
                response = self._parent.matcher_response(response)
                return response
            elif ret == -1:
                return self._parent.send_error(request, response, 'METHOD_NOT_ALLOWED')
            else:
                return self._parent.send_error(request, response, 'INTERNAL_SERVER_ERROR')
        else:
            return self._parent.send_error(request, response, 'METHOD_NOT_ALLOWED')

    def get_resource(self, request, response, resource):
        """
        Render a GET request.

        :param request: the request
        :param response: the response
        :param resource: the resource required
        :return: the response
        """
        method = getattr(resource, 'render_GET', None)
        if hasattr(method, '__call__'):
            resource.required_content_type = None
            #Accept
            if request.accept is not None:
                resource.required_content_type = request.accept
                if resource.required_content_type in defines.content_types:
                    response.content_type = resource.required_content_type
            # Render_GET
            t = Timer(defines.SEPARATE_TIMEOUT, self.send_ack, [request])
            t.start()
            ret = method(request=request, query=request.query)
            t.cancel()
            if isinstance(ret, dict):
                etag = ret.get("ETag")
                max_age = ret.get("Max-Age")
                separate = ret.get("Separate")
                callback = ret.get("Callback")
                ret = ret.get("Payload")
            else:
                etag = None
                max_age = None
                separate = None
                callback = None
            if separate is not None:
                # Handle separate
                self.send_ack(request)
                ret = callback(request=request, query=request.query)
                if isinstance(ret, dict):
                    etag = ret.get("ETag")
                    max_age = ret.get("Max-Age")
                    ret = ret.get("Payload")
                else:
                    etag = None
                    max_age = None
            if ret != -1:
                if ret == -2:
                    response = self._parent.send_error(request, response, 'NOT_ACCEPTABLE')
                    return response
                # handle ETAG
                if etag in request.etag:
                    response.code = defines.responses['VALID']
                else:
                    response.code = defines.responses['CONTENT']
                    response.payload = ret
                response.token = request.token
                if etag is not None:
                    response.etag = etag
                if max_age is not None:
                    response.max_age = max_age

                # Observe
                if request.observe == 0 and resource.observable:
                    response = self._parent.add_observing(resource, response)
                #TODO Blockwise
                response = self._parent.reliability_response(request, response)
                response = self._parent.matcher_response(response)
            else:
                response = self._parent.send_error(request, response, 'METHOD_NOT_ALLOWED')
        else:
            response = self._parent.send_error(request, response, 'METHOD_NOT_ALLOWED')
        return response

    def discover(self, request, response):
        """
        Render a GET request to the .weel-know/core link.

        :param request: the request
        :param response: the response
        :return: the response
        """
        node = self._parent.root
        assert isinstance(node, Tree)
        response.code = defines.responses['CONTENT']
        response.payload = node.corelinkformat()
        response.content_type = defines.inv_content_types["application/link-format"]
        response.token = request.token
        #TODO Blockwise
        response = self._parent.reliability_response(request, response)
        response = self._parent.matcher_response(response)
        return response

    def create_subtree(self, paths):
        node = self._parent.root
        assert isinstance(paths, list)
        assert isinstance(node, Tree)
        last = None
        while True:
            last, failed_resource = node.find_complete_last(paths)
            if failed_resource is None:
                break
            resource = Resource(name="subtree", visible=True, observable=False, allow_children=True)
            method = getattr(resource, "new_resource", None)
            resource = method()
            resource.payload = None
            resource.path = failed_resource
            last.add_child(resource)
        return last

    def send_ack(self, *args):
        # Handle separate
        """
        Sends an ACK message for the request.

        :param args: [request]
        """
        request = args[0]
        ack = Message.new_ack(request)
        host, port = request.source
        self._parent.send(ack, host, port)
        request.acknowledged = True