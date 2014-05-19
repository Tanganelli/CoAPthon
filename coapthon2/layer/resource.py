from coapthon2 import defines
from coapthon2.utils import Tree

__author__ = 'giacomo'


class ResourceLayer(object):
    def __init__(self, parent):
        self._parent = parent

    def create_resource(self, path, request, response, render_method="render_PUT"):
        paths = path.split("/")
        old = self._parent.root
        for p in paths:
            res = old.find(p)
            if res is None:
                if old.value.allow_children:
                    method = getattr(old.value, render_method, None)
                    if hasattr(method, '__call__'):
                        resource = method(payload=request.payload, query=request.query)
                        if resource is not None and resource != -1:
                            resource.path = p
                            old = old.add_child(resource)
                            if render_method == "render_PUT":
                                response.code = defines.responses['CHANGED']
                            else:
                                response.code = defines.responses['CREATED']
                            response.payload = None
                            # Token
                            response.token = request.token
                            # Observe
                            self._parent.notify(old.parent)
                            #TODO Blockwise
                            #Reliability
                            response = self._parent.reliability_response(request, response)
                            #Matcher
                            response = self._parent.matcher_response(response)
                            return response
                        elif resource == -1:
                            return self._parent.send_error(request, response, 'METHOD_NOT_ALLOWED')
                        else:
                            return self._parent.send_error(request, response, 'INTERNAL_SERVER_ERROR')
                    else:
                        return self._parent.send_error(request, response, 'METHOD_NOT_ALLOWED')
                else:
                    return self._parent.send_error(request, response, 'METHOD_NOT_ALLOWED')
            else:
                old = res

    def update_resource(self, path, request, response, resource, render_method="render_PUT"):
        path = path.strip("/")
        node = self._parent.root.find_complete(path)
        method = getattr(resource, render_method, None)
        if hasattr(method, '__call__'):
            new_resource = method(create=False, payload=request.payload, query=request.query)
            if new_resource is not None and new_resource != -1:
                node.value = new_resource
                if render_method == "render_PUT":
                    response.code = defines.responses['CHANGED']
                else:
                    response.code = defines.responses['CREATED']
                response.payload = None
                # Token
                response.token = request.token
                # Observe
                self._parent.notify(node)
                #TODO Blockwise
                #Reliability
                response = self._parent.reliability_response(request, response)
                #Matcher
                response = self._parent.matcher_response(response)
                return response
            elif new_resource == -1:
                return self._parent.send_error(request, response, 'METHOD_NOT_ALLOWED')
            else:
                return self._parent.send_error(request, response, 'INTERNAL_SERVER_ERROR')
        else:
            return self._parent.send_error(request, response, 'METHOD_NOT_ALLOWED')

    def delete_resource(self, request, response, node):
        assert isinstance(node, Tree)
        method = getattr(node.value, 'render_DELETE', None)
        if hasattr(method, '__call__'):
            ret = method(query=request.query)
            if ret != -1:
                parent = node.parent
                assert isinstance(parent, Tree)
                # Observe
                self._parent.notify(parent)
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
        method = getattr(resource, 'render_GET', None)
        if hasattr(method, '__call__'):
            #TODO handle ETAG

            if resource.content_type != "":
                    resource.required_content_type = "text/plain"
                    response.content_type = resource.required_content_type
            # Render_GET
            ret = method(query=request.query)
            if ret != -1:
                response.code = defines.responses['CONTENT']
                response.token = request.token
                response.payload = ret
                # Observe
                if request.observe and resource.observable:
                    response, resource = self._parent.add_observing(resource, response)
                #TODO Blockwise
                response = self._parent.reliability_response(request, response)
                response = self._parent.matcher_response(response)
            else:
                response = self._parent.send_error(request, response, 'METHOD_NOT_ALLOWED')
        else:
            response = self._parent.send_error(request, response, 'METHOD_NOT_ALLOWED')
        return response

    def discover(self, request, response):
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