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
                        resource = method()
                        if resource is not None:
                            resource.path = p
                            old = old.add_child(resource)
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
            new_resource = method(False, request.payload)
            if new_resource is not None:
                node.value = new_resource
                response.code = defines.responses['CHANGED']
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
            else:
                return self._parent.send_error(request, response, 'INTERNAL_SERVER_ERROR')
        else:
            return self._parent.send_error(request, response, 'METHOD_NOT_ALLOWED')

    def delete_resource(self, request, response, node):
        assert isinstance(node, Tree)
        method = getattr(node.value, 'render_DELETE', None)
        if hasattr(method, '__call__'):
            ret = method()
            if ret:
                parent = node.parent
                assert isinstance(parent, Tree)
                # Observe
                self._parent.notify(parent)
                self._parent.remove_observes(node)

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
            else:
                return self._parent.send_error(request, response, 'INTERNAL_SERVER_ERROR')
        else:
            return self._parent.end_error(request, response, 'METHOD_NOT_ALLOWED')

    def get_resource(self, request, response, resource):
        method = getattr(resource, 'render_GET', None)
        if hasattr(method, '__call__'):
            #TODO handle ETAG
            # Render_GET
            response.code = defines.responses['CONTENT']
            response.payload = method()
            response.token = request.token
            # Observe
            if request.observe and resource.observable:
                response, resource = self._parent.add_observing(resource, response)
            #TODO Blockwise
            response = self._parent.reliability_response(request, response)
            response = self._parent.matcher_response(response)
        else:
            response = self._parent.send_error(request, response, 'METHOD_NOT_ALLOWED')
        return response