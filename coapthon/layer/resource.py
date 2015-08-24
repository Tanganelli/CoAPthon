from coapthon import defines
from coapthon.resources.resource import Resource

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

    def edit_resource(self, request, response, path):
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
        resource_node = self._parent.root[path]

        method = getattr(resource_node, "render_POST", None)
        if hasattr(method, '__call__'):
            timer = self._parent.message_layer.start_separate_timer(request)
            resource = method(request=request)
            stopped = self._parent.message_layer.stop_separate_timer(timer)
            separate = False
            callback = None
            if isinstance(resource, Resource):
                pass
            elif isinstance(resource, int):
                return self._parent.send_error(request, response, 'METHOD_NOT_ALLOWED')
            elif isinstance(resource, tuple) and len(resource) == 2:
                resource, callback = resource
                separate = True
            else:
                # Handle error
                return self._parent.send_error(request, response, 'INTERNAL_SERVER_ERROR')

            if separate:
                # Handle separate
                if stopped:
                    self._parent.message_layer.send_separate(request)
                    request.acknowledged = True
                resource = callback(request=request)
                if not isinstance(resource, Resource):
                    return self._parent.send_error(request, response, 'INTERNAL_SERVER_ERROR')

            resource.path = path
            resource.observe_count = resource_node.observe_count

            response.code = defines.responses['CREATED']
            # Blockwise
            response, resource = self._parent.blockwise_response(request, response, resource)

            # Observe
            self._parent.observe_layer.update_relations(path, resource)

            self._parent.notify(resource)

            if resource.etag is not None:
                response.etag = resource.etag

            response.location_path = path

            if resource.location_query is not None and len(resource.location_query) > 0:
                response.location_query = resource.location_query

            response.payload = None
            # Token
            response.token = request.token
            # Reliability
            response = self._parent.message_layer.reliability_response(request, response)
            # Matcher
            response = self._parent.message_layer.matcher_response(response)

            self._parent.root[path] = resource

            return response
        else:
            return self._parent.send_error(request, response, 'METHOD_NOT_ALLOWED')

    def add_resource(self, request, response, parent_resource, lp):
        """
        Render a POST on a new resource.

        :type old: coapthon2.utils.Tree
        :param request: the request
        :param response: the response
        :param old: the node which has the parent of the resource
        :param lp: the location_path attribute of the resource
        :param p: the local path of the resource (only the last section of the split path)
        :return: the response
        """
        method = getattr(parent_resource, "render_POST", None)
        if hasattr(method, '__call__'):
            timer = self._parent.message_layer.start_separate_timer(request)
            resource = method(request=request)
            stopped = self._parent.message_layer.stop_separate_timer(timer)
            separate = False
            callback = None
            if isinstance(resource, Resource):
                pass
            elif isinstance(resource, int):
                return self._parent.send_error(request, response, 'METHOD_NOT_ALLOWED')
            elif isinstance(resource, tuple) and len(resource) == 2:
                resource, callback = resource
                separate = True
            else:
                # Handle error
                return self._parent.send_error(request, response, 'INTERNAL_SERVER_ERROR')

            if separate:
                # Handle separate
                if stopped:
                    self._parent.message_layer.send_separate(request)
                    request.acknowledged = True
                resource = callback(request=request)
                if not isinstance(resource, Resource):
                    return self._parent.send_error(request, response, 'INTERNAL_SERVER_ERROR')

            resource.path = lp

            if resource.etag is not None:
                response.etag = resource.etag

            response.location_path = lp

            if resource.location_query is not None and len(resource.location_query) > 0:
                response.location_query = resource.location_query

            response.code = defines.responses['CREATED']
            response.payload = None

            # Token
            response.token = request.token

            # Blockwise
            response, resource = self._parent.blockwise_response(request, response, resource)

            # Reliability
            response = self._parent.message_layer.reliability_response(request, response)
            # Matcher
            response = self._parent.message_layer.matcher_response(response)

            self._parent.root[lp] = resource

            return response

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
        t = self._parent.root.with_prefix(path)
        max_len = 0
        imax = None
        for i in t:
            if i == path:
                # Resource already present
                return self.edit_resource(request, response, path)
            elif len(i) > max_len:
                imax = i
                max_len = len(i)

        lp = path
        parent_resource = self._parent.root[imax]
        if parent_resource.allow_children:
                return self.add_resource(request, response, parent_resource, lp)
        else:
            return self._parent.send_error(request, response, 'METHOD_NOT_ALLOWED')

    def update_resource(self, request, response, resource):
        """
        Render a PUT request.

        :type node: coapthon2.utils.Tree
        :param request: the request
        :param response: the response
        :param node: the node which has the resource
        :return: the response
        """
        # If-Match
        if request.has_if_match:
            if None not in request.if_match and str(resource.etag) not in request.if_match:
                return self._parent.send_error(request, response, 'PRECONDITION_FAILED')
        # If-None-Match
        if request.has_if_none_match:
            return self._parent.send_error(request, response, 'PRECONDITION_FAILED')
        method = getattr(resource, "render_PUT", None)
        if hasattr(method, '__call__'):
            timer = self._parent.message_layer.start_separate_timer(request)
            resource = method(request=request)
            stopped = self._parent.message_layer.stop_separate_timer(timer)
            separate = False
            callback = None
            if isinstance(resource, Resource):
                pass
            elif isinstance(resource, int):
                return self._parent.send_error(request, response, 'METHOD_NOT_ALLOWED')
            elif isinstance(resource, tuple) and len(resource) == 2:
                resource, callback = resource
                separate = True
            else:
                # Handle error
                return self._parent.send_error(request, response, 'INTERNAL_SERVER_ERROR')
            if separate:
                # Handle separate
                if stopped:
                    self._parent.message_layer.send_separate(request)
                    request.acknowledged = True
                resource = callback(request=request)
                if not isinstance(resource, Resource):
                    return self._parent.send_error(request, response, 'INTERNAL_SERVER_ERROR')

            if resource.etag is not None:
                    response.etag = resource.etag

            response.code = defines.responses['CHANGED']
            response.payload = None
            # Token
            response.token = request.token
            # Blockwise
            response, resource = self._parent.blockwise_response(request, response, resource)
            # TODO check PUT Blockwise
            # Observe
            self._parent.notify(resource)

            # Reliability
            response = self._parent.message_layer.reliability_response(request, response)
            # Matcher
            response = self._parent.message_layer.matcher_response(response)

            return response
        else:
            return self._parent.send_error(request, response, 'METHOD_NOT_ALLOWED')

    def delete_resource(self, request, response, path):
        """
        Render a DELETE request.

        :param request: the request
        :param response: the response
        :param path: the path
        :return: the response
        """
        try:
            resource = self._parent.root[path]
        except KeyError:
            resource = None

        method = getattr(resource, 'render_DELETE', None)
        if hasattr(method, '__call__'):
            timer = self._parent.message_layer.start_separate_timer(request)
            ret = method(request=request)
            self._parent.message_layer.stop_separate_timer(timer)
            if ret != -1:
                # Observe
                self._parent.notify_deletion(resource)
                self._parent.remove_observers(path)

                del self._parent.root[path]
                response.code = defines.responses['DELETED']
                response.payload = None
                # Token
                response.token = request.token
                # Reliability
                response = self._parent.message_layer.reliability_response(request, response)
                # Matcher
                response = self._parent.message_layer.matcher_response(response)
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
            # Accept
            if request.accept is not None:
                resource.required_content_type = request.accept
                if resource.required_content_type in defines.content_types:
                    response.content_type = resource.required_content_type
            # Render_GET
            timer = self._parent.message_layer.start_separate_timer(request)
            resource = method(request=request)
            stopped = self._parent.message_layer.stop_separate_timer(timer)
            separate = False
            callback = None
            if isinstance(resource, Resource):
                pass
            elif isinstance(resource, int):
                return self._parent.send_error(request, response, 'METHOD_NOT_ALLOWED')
            elif isinstance(resource, tuple) and len(resource) == 2:
                resource, callback = resource
                separate = True
            else:
                # Handle error
                return self._parent.send_error(request, response, 'INTERNAL_SERVER_ERROR')
            if separate:
                # Handle separate
                if stopped:
                    self._parent.message_layer.send_separate(request)
                    request.acknowledged = True
                resource = callback(request=request)
                if not isinstance(resource, Resource):
                    return self._parent.send_error(request, response, 'NOT_ACCEPTABLE')

            if resource.etag in request.etag:
                response.code = defines.responses['VALID']
            else:
                response.code = defines.responses['CONTENT']

            try:
                response.payload = resource.payload
            except KeyError:
                return self._parent.send_error(request, response, 'NOT_ACCEPTABLE')

            # Blockwise
            response, resource = self._parent.blockwise_response(request, response, resource)

            response.token = request.token
            if resource.etag is not None:
                response.etag = resource.etag
            if resource.max_age is not None:
                response.max_age = resource.max_age

            # Observe
            if request.observe == 0 and resource.observable:
                response = self._parent.observe_layer.add_observing(resource, request, response)

            response = self._parent.message_layer.reliability_response(request, response)
            response = self._parent.message_layer.matcher_response(response)

            return response
        else:
            return self._parent.send_error(request, response, 'METHOD_NOT_ALLOWED')

    def discover(self, request, response):
        """
        Render a GET request to the .weel-know/core link.

        :param request: the request
        :param response: the response
        :return: the response
        """
        response.code = defines.responses['CONTENT']
        payload = ""
        for i in self._parent.root.dump():
            if i == "/":
                continue
            resource = self._parent.root[i]
            payload += self.corelinkformat(resource)

        response.payload = payload
        response.content_type = defines.inv_content_types["application/link-format"]
        response.token = request.token
        # Blockwise
        response, resource = self._parent.blockwise_response(request, response, None)
        response = self._parent.message_layer.reliability_response(request, response)
        response = self._parent.message_layer.matcher_response(response)
        return response

    @staticmethod
    def corelinkformat(resource):
        """
        Return a formatted string representation of the corelinkformat in the tree.

        :return: the string
        """
        msg = "<" + resource.path + ">;"
        assert(isinstance(resource, Resource))
        for k in resource.attributes:
            method = getattr(resource, defines.corelinkformat[k], None)
            if method is not None and method != "":
                v = method
                msg = msg[:-1] + ";" + str(v) + ","
            else:
                v = resource.attributes[k]
                if v is not None:
                    msg = msg[:-1] + ";" + k + "=" + v + ","
        return msg