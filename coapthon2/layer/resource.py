from coapthon2 import defines
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

    def edit_resource(self, request, response, node, lp, p):
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
            timer = self._parent.start_separate_timer(request)
            resource = method(request=request)
            stopped = self._parent.stop_separate_timer(timer)
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
                    self._parent.send_separate(request)
                    request.acknowledged = True
                resource = callback(request=request)
                if not isinstance(resource, Resource):
                    return self._parent.send_error(request, response, 'INTERNAL_SERVER_ERROR')

            resource.path = p
            resource.observe_count = node.value.observe_count

            response.code = defines.responses['CREATED']
            # Blockwise
            response, resource = self._parent.blockwise_response(request, response, resource)

            # Observe
            self._parent.update_relations(node, resource)

            self._parent.notify(resource)

            if resource.etag is not None:
                response.etag = resource.etag

            response.location_path = lp

            if resource.location_query is not None and len(resource.location_query) > 0:
                response.location_query = resource.location_query

            response.payload = None
            # Token
            response.token = request.token
            # Reliability
            response = self._parent.reliability_response(request, response)
            # Matcher
            response = self._parent.matcher_response(response)

            node.value = resource

            return response
        else:
            return self._parent.send_error(request, response, 'METHOD_NOT_ALLOWED')

    def add_resource(self, request, response, old, lp, p):
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
        method = getattr(old.value, "render_POST", None)
        if hasattr(method, '__call__'):
            timer = self._parent.start_separate_timer(request)
            resource = method(request=request)
            stopped = self._parent.stop_separate_timer(timer)
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
                    self._parent.send_separate(request)
                    request.acknowledged = True
                resource = callback(request=request)
                if not isinstance(resource, Resource):
                    return self._parent.send_error(request, response, 'INTERNAL_SERVER_ERROR')

            resource.path = p

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
            response = self._parent.reliability_response(request, response)
            # Matcher
            response = self._parent.matcher_response(response)

            old.value = resource

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
        paths = path.split("/")
        last, p = self._parent.root.find_complete_last(paths)
        if p is None:
            # Resource already present
            return self.edit_resource(request, response, last, path, paths[-1])
        else:
            lp = last.find_path() + p
            if last.value.allow_children:
                    return self.add_resource(request, response, last, lp[1:], p)
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
            timer = self._parent.start_separate_timer(request)
            resource = method(request=request)
            stopped = self._parent.stop_separate_timer(timer)
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
                    self._parent.send_separate(request)
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
            response = self._parent.reliability_response(request, response)
            # Matcher
            response = self._parent.matcher_response(response)

            node.value = resource
            return response
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
            timer = self._parent.start_separate_timer(request)
            ret = method(request=request)
            self._parent.stop_separate_timer(timer)
            if ret != -1:
                parent = node.parent
                assert isinstance(parent, Tree)
                # Observe
                resource = node.value
                self._parent.notify_deletion(resource)
                self._parent.remove_observers(node)

                parent.del_child(node)
                response.code = defines.responses['DELETED']
                response.payload = None
                # Token
                response.token = request.token
                # Reliability
                response = self._parent.reliability_response(request, response)
                # Matcher
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
            # Accept
            if request.accept is not None:
                resource.required_content_type = request.accept
                if resource.required_content_type in defines.content_types:
                    response.content_type = resource.required_content_type
            # Render_GET
            timer = self._parent.start_separate_timer(request)
            resource = method(request=request)
            stopped = self._parent.stop_separate_timer(timer)
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
                    self._parent.send_separate(request)
                    request.acknowledged = True
                resource = callback(request=request)
                if not isinstance(resource, Resource):
                    return self._parent.send_error(request, response, 'NOT_ACCEPTABLE')

            if resource.etag in request.etag:
                response.code = defines.responses['VALID']
            else:
                response.code = defines.responses['CONTENT']

            response.payload = resource.payload

            # Blockwise
            response, resource = self._parent.blockwise_response(request, response, resource)

            response.token = request.token
            if resource.etag is not None:
                response.etag = resource.etag
            if resource.max_age is not None:
                response.max_age = resource.max_age

            # Observe
            if request.observe == 0 and resource.observable:
                response = self._parent.add_observing(resource, request, response)

            response = self._parent.reliability_response(request, response)
            response = self._parent.matcher_response(response)

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
        node = self._parent.root
        assert isinstance(node, Tree)
        response.code = defines.responses['CONTENT']
        response.payload = node.corelinkformat()
        response.content_type = defines.inv_content_types["application/link-format"]
        response.token = request.token
        # Blockwise
        response, resource = self._parent.blockwise_response(request, response, None)
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