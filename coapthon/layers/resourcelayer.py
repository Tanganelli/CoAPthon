from coapthon import defines
from coapthon.messages.response import Response
from coapthon.resources.resource import Resource

__author__ = 'Giacomo Tanganelli'


class ResourceLayer(object):
    """
    Handles the Resources.
    """
    def __init__(self, parent):
        """
        Initialize a Resource Layer.

        :type parent: CoAP
        :param parent: the CoAP server
        """
        self._parent = parent

    def edit_resource(self, transaction, path):
        """
        Render a POST on an already created resource.

        :param path: the path of the resource
        :param transaction: the transaction
        :return: the transaction
        """
        resource_node = self._parent.root[path]
        transaction.resource = resource_node
        # If-Match
        if transaction.request.if_match:
            if None not in transaction.request.if_match and str(transaction.resource.etag) \
                    not in transaction.request.if_match:
                transaction.response.code = defines.Codes.PRECONDITION_FAILED.number
                return transaction

        method = getattr(resource_node, "render_POST", None)
        try:
            resource = method(request=transaction.request)
        except NotImplementedError:
            try:
                method = getattr(resource_node, "render_POST_advanced", None)
                ret = method(request=transaction.request, response=transaction.response)
                if isinstance(ret, tuple) and len(ret) == 2 and isinstance(ret[1], Response) \
                        and isinstance(ret[0], Resource):
                    # Advanced handler
                    resource, response = ret
                    resource.changed = True
                    resource.observe_count += 1
                    transaction.resource = resource
                    transaction.response = response
                    if transaction.response.code is None:
                        transaction.response.code = defines.Codes.CREATED.number
                    return transaction
                elif isinstance(ret, tuple) and len(ret) == 3 and isinstance(ret[1], Response) \
                        and isinstance(ret[0], Resource):
                    # Advanced handler separate
                    resource, response, callback = ret
                    ret = self._handle_separate_advanced(transaction, callback)
                    if not isinstance(ret, tuple) or \
                            not (isinstance(ret[0], Resource) and isinstance(ret[1], Response)):  # pragma: no cover
                        transaction.response.code = defines.Codes.INTERNAL_SERVER_ERROR.number
                        return transaction
                    resource, response = ret
                    resource.changed = True
                    resource.observe_count += 1
                    transaction.resource = resource
                    transaction.response = response
                    if transaction.response.code is None:
                        transaction.response.code = defines.Codes.CREATED.number
                    return transaction
                else:
                    raise NotImplementedError
            except NotImplementedError:
                transaction.response.code = defines.Codes.METHOD_NOT_ALLOWED.number
                return transaction

        if isinstance(resource, Resource):
            pass
        elif isinstance(resource, tuple) and len(resource) == 2:
            resource, callback = resource
            resource = self._handle_separate(transaction, callback)
            if not isinstance(resource, Resource):  # pragma: no cover
                transaction.response.code = defines.Codes.INTERNAL_SERVER_ERROR.number
                return transaction
        else:  # pragma: no cover
            # Handle error
            transaction.response.code = defines.Codes.INTERNAL_SERVER_ERROR.number
            return transaction

        if resource.path is None:
            resource.path = path
        resource.observe_count = resource_node.observe_count

        if resource is resource_node:
            transaction.response.code = defines.Codes.CHANGED.number
        else:
            transaction.response.code = defines.Codes.CREATED.number
        resource.changed = True
        resource.observe_count += 1
        transaction.resource = resource

        assert(isinstance(resource, Resource))
        if resource.etag is not None:
            transaction.response.etag = resource.etag

        transaction.response.location_path = resource.path

        if resource.location_query is not None and len(resource.location_query) > 0:
            transaction.response.location_query = resource.location_query

        transaction.response.payload = None

        self._parent.root[resource.path] = resource

        return transaction

    def add_resource(self, transaction, parent_resource, lp):
        """
        Render a POST on a new resource.

        :param transaction: the transaction
        :param parent_resource: the parent of the resource
        :param lp: the location_path attribute of the resource
        :return: the response
        """
        method = getattr(parent_resource, "render_POST", None)
        try:
            resource = method(request=transaction.request)
        except NotImplementedError:
            try:
                method = getattr(parent_resource, "render_POST_advanced", None)
                ret = method(request=transaction.request, response=transaction.response)
                if isinstance(ret, tuple) and len(ret) == 2 and isinstance(ret[1], Response) \
                        and isinstance(ret[0], Resource):
                    # Advanced handler
                    resource, response = ret
                    resource.path = lp
                    resource.changed = True
                    self._parent.root[resource.path] = resource
                    transaction.resource = resource
                    transaction.response = response
                    if transaction.response.code is None:
                        transaction.response.code = defines.Codes.CREATED.number
                    return transaction
                elif isinstance(ret, tuple) and len(ret) == 3 and isinstance(ret[1], Response) \
                        and isinstance(ret[0], Resource):
                    # Advanced handler separate
                    resource, response, callback = ret
                    ret = self._handle_separate_advanced(transaction, callback)
                    if not isinstance(ret, tuple) or \
                            not (isinstance(ret[0], Resource) and isinstance(ret[1], Response)):  # pragma: no cover
                        transaction.response.code = defines.Codes.INTERNAL_SERVER_ERROR.number
                        return transaction
                    resource, response = ret
                    resource.path = lp
                    resource.changed = True
                    self._parent.root[resource.path] = resource
                    transaction.resource = resource
                    transaction.response = response
                    if transaction.response.code is None:
                        transaction.response.code = defines.Codes.CREATED.number
                    return transaction
                else:
                    raise NotImplementedError
            except NotImplementedError:
                transaction.response.code = defines.Codes.METHOD_NOT_ALLOWED.number
                return transaction
        if isinstance(resource, Resource):
            pass
        elif isinstance(resource, tuple) and len(resource) == 2:
            resource, callback = resource
            resource = self._handle_separate(transaction, callback)
            if not isinstance(resource, Resource):  # pragma: no cover
                transaction.response.code = defines.Codes.INTERNAL_SERVER_ERROR.number
                return transaction
        else:  # pragma: no cover
            # Handle error
            transaction.response.code = defines.Codes.INTERNAL_SERVER_ERROR.number
            return transaction

        resource.path = lp

        if resource.etag is not None:
            transaction.response.etag = resource.etag

        transaction.response.location_path = resource.path

        if resource.location_query is not None and len(resource.location_query) > 0:
            transaction.response.location_query = resource.location_query

        transaction.response.code = defines.Codes.CREATED.number
        transaction.response.payload = None

        assert (isinstance(resource, Resource))
        if resource.etag is not None:
            transaction.response.etag = resource.etag
        if resource.max_age is not None:
            transaction.response.max_age = resource.max_age

        resource.changed = True

        transaction.resource = resource

        self._parent.root[resource.path] = resource

        return transaction

    def create_resource(self, path, transaction):
        """
        Render a POST request.

        :param path: the path of the request
        :param transaction: the transaction
        :return: the response
        """
        t = self._parent.root.with_prefix(path)
        max_len = 0
        imax = None
        for i in t:
            if i == path:
                # Resource already present
                return self.edit_resource(transaction, path)
            elif len(i) > max_len:
                imax = i
                max_len = len(i)

        lp = path
        parent_resource = self._parent.root[imax]
        if parent_resource.allow_children:
                return self.add_resource(transaction, parent_resource, lp)
        else:
            transaction.response.code = defines.Codes.METHOD_NOT_ALLOWED.number
            return transaction

    def update_resource(self, transaction):
        """
        Render a PUT request.

        :param transaction: the transaction
        :return: the response
        """
        # If-Match
        if transaction.request.if_match:
            if None not in transaction.request.if_match and str(transaction.resource.etag) \
                    not in transaction.request.if_match:
                transaction.response.code = defines.Codes.PRECONDITION_FAILED.number
                return transaction
        # If-None-Match
        if transaction.request.if_none_match:
            transaction.response.code = defines.Codes.PRECONDITION_FAILED.number
            return transaction

        method = getattr(transaction.resource, "render_PUT", None)

        try:
            resource = method(request=transaction.request)
        except NotImplementedError:
            try:
                method = getattr(transaction.resource, "render_PUT_advanced", None)
                ret = method(request=transaction.request, response=transaction.response)
                if isinstance(ret, tuple) and len(ret) == 2 and isinstance(ret[1], Response) \
                        and isinstance(ret[0], Resource):
                    # Advanced handler
                    resource, response = ret
                    resource.changed = True
                    resource.observe_count += 1
                    transaction.resource = resource
                    transaction.response = response
                    if transaction.response.code is None:
                        transaction.response.code = defines.Codes.CHANGED.number
                    return transaction
                elif isinstance(ret, tuple) and len(ret) == 3 and isinstance(ret[1], Response) \
                        and isinstance(ret[0], Resource):
                    # Advanced handler separate
                    resource, response, callback = ret
                    ret = self._handle_separate_advanced(transaction, callback)
                    if not isinstance(ret, tuple) or \
                            not (isinstance(ret[0], Resource) and isinstance(ret[1], Response)):  # pragma: no cover
                        transaction.response.code = defines.Codes.INTERNAL_SERVER_ERROR.number
                        return transaction
                    resource, response = ret
                    resource.changed = True
                    resource.observe_count += 1
                    transaction.resource = resource
                    transaction.response = response
                    if transaction.response.code is None:
                        transaction.response.code = defines.Codes.CHANGED.number
                    return transaction
                else:
                    raise NotImplementedError
            except NotImplementedError:
                transaction.response.code = defines.Codes.METHOD_NOT_ALLOWED.number
                return transaction

        if isinstance(resource, Resource):
            pass
        elif isinstance(resource, tuple) and len(resource) == 2:
            resource, callback = resource
            resource = self._handle_separate(transaction, callback)
            if not isinstance(resource, Resource):  # pragma: no cover
                transaction.response.code = defines.Codes.INTERNAL_SERVER_ERROR.number
                return transaction
        else:  # pragma: no cover
            # Handle error
            transaction.response.code = defines.Codes.INTERNAL_SERVER_ERROR.number
            return transaction

        if resource.etag is not None:
            transaction.response.etag = resource.etag

        transaction.response.code = defines.Codes.CHANGED.number

        transaction.response.payload = None

        assert (isinstance(resource, Resource))
        if resource.etag is not None:
            transaction.response.etag = resource.etag
        if resource.max_age is not None:
            transaction.response.max_age = resource.max_age

        resource.changed = True
        resource.observe_count += 1
        transaction.resource = resource

        return transaction

    def _handle_separate(self, transaction, callback):
        # Handle separate
        if not transaction.request.acknowledged:
            self._parent._send_ack(transaction)
            transaction.request.acknowledged = True
        resource = callback(request=transaction.request)
        return resource

    def _handle_separate_advanced(self, transaction, callback):
        # Handle separate
        if not transaction.request.acknowledged:
            self._parent._send_ack(transaction)
            transaction.request.acknowledged = True
        return callback(request=transaction.request, response=transaction.response)

    def delete_resource(self, transaction, path):
        """
        Render a DELETE request.

        :param transaction: the transaction
        :param path: the path
        :return: the response
        """

        resource = transaction.resource
        method = getattr(resource, 'render_DELETE', None)

        try:
            ret = method(request=transaction.request)
        except NotImplementedError:
            try:
                method = getattr(transaction.resource, "render_DELETE_advanced", None)
                ret = method(request=transaction.request, response=transaction.response)
                if isinstance(ret, tuple) and len(ret) == 2 and isinstance(ret[1], Response) \
                        and isinstance(ret[0], bool):
                    # Advanced handler
                    delete, response = ret
                    if delete:
                        del self._parent.root[path]
                    transaction.response = response
                    if transaction.response.code is None:
                        transaction.response.code = defines.Codes.DELETED.number
                    return transaction
                elif isinstance(ret, tuple) and len(ret) == 3 and isinstance(ret[1], Response) \
                        and isinstance(ret[0], Resource):
                    # Advanced handler separate
                    resource, response, callback = ret
                    ret = self._handle_separate_advanced(transaction, callback)
                    if not isinstance(ret, tuple) or \
                            not (isinstance(ret[0], bool) and isinstance(ret[1], Response)):  # pragma: no cover
                        transaction.response.code = defines.Codes.INTERNAL_SERVER_ERROR.number
                        return transaction
                    delete, response = ret
                    if delete:
                        del self._parent.root[path]
                    transaction.response = response
                    if transaction.response.code is None:
                        transaction.response.code = defines.Codes.DELETED.number
                    return transaction
                else:
                    raise NotImplementedError
            except NotImplementedError:
                transaction.response.code = defines.Codes.METHOD_NOT_ALLOWED.number
                return transaction

        if isinstance(ret, bool):
            pass
        elif isinstance(ret, tuple) and len(ret) == 2:
            resource, callback = ret
            ret = self._handle_separate(transaction, callback)
            if not isinstance(ret, bool):  # pragma: no cover
                transaction.response.code = defines.Codes.INTERNAL_SERVER_ERROR.number
                return transaction
        else:  # pragma: no cover
            # Handle error
            transaction.response.code = defines.Codes.INTERNAL_SERVER_ERROR.number
            return transaction
        if ret:
            del self._parent.root[path]
            transaction.response.code = defines.Codes.DELETED.number
            transaction.response.payload = None
            transaction.resource.deleted = True
        else:  # pragma: no cover
            transaction.response.code = defines.Codes.INTERNAL_SERVER_ERROR.number

        return transaction

    def get_resource(self, transaction):
        """
        Render a GET request.

        :param transaction: the transaction
        :return: the transaction
        """
        method = getattr(transaction.resource, 'render_GET', None)

        transaction.resource.actual_content_type = None
        # Accept
        if transaction.request.accept is not None:
            transaction.resource.actual_content_type = transaction.request.accept

        # Render_GET
        try:
            resource = method(request=transaction.request)
        except NotImplementedError:
            try:
                method = getattr(transaction.resource, "render_GET_advanced", None)
                ret = method(request=transaction.request, response=transaction.response)
                if isinstance(ret, tuple) and len(ret) == 2 and isinstance(ret[1], Response) \
                        and isinstance(ret[0], Resource):
                    # Advanced handler
                    resource, response = ret
                    transaction.resource = resource
                    transaction.response = response
                    if transaction.response.code is None:
                        transaction.response.code = defines.Codes.CONTENT.number
                    return transaction
                elif isinstance(ret, tuple) and len(ret) == 3 and isinstance(ret[1], Response) \
                        and isinstance(ret[0], Resource):
                    # Advanced handler separate
                    resource, response, callback = ret
                    ret = self._handle_separate_advanced(transaction, callback)
                    if not isinstance(ret, tuple) or \
                            not (isinstance(ret[0], Resource) and isinstance(ret[1], Response)):  # pragma: no cover
                        transaction.response.code = defines.Codes.INTERNAL_SERVER_ERROR.number
                        return transaction
                    resource, response = ret
                    transaction.resource = resource
                    transaction.response = response
                    if transaction.response.code is None:
                        transaction.response.code = defines.Codes.CONTENT.number
                    return transaction
                else:
                    raise NotImplementedError
            except NotImplementedError:
                transaction.response.code = defines.Codes.METHOD_NOT_ALLOWED.number
                return transaction

        if isinstance(resource, Resource):
            pass
        elif isinstance(resource, tuple) and len(resource) == 2:
            resource, callback = resource
            resource = self._handle_separate(transaction, callback)
            if not isinstance(resource, Resource):  # pragma: no cover
                transaction.response.code = defines.Codes.INTERNAL_SERVER_ERROR.number
                return transaction
        else:  # pragma: no cover
            # Handle error
            transaction.response.code = defines.Codes.INTERNAL_SERVER_ERROR.number
            return transaction.response

        if resource.etag in transaction.request.etag:
            transaction.response.code = defines.Codes.VALID.number
        else:
            transaction.response.code = defines.Codes.CONTENT.number

        try:
            transaction.response.payload = resource.payload
            if resource.actual_content_type is not None \
                    and resource.actual_content_type != defines.Content_types["text/plain"]:
                transaction.response.content_type = resource.actual_content_type
        except KeyError:
            transaction.response.code = defines.Codes.NOT_ACCEPTABLE.number
            return transaction.response

        assert(isinstance(resource, Resource))
        if resource.etag is not None:
            transaction.response.etag = resource.etag
        if resource.max_age is not None:
            transaction.response.max_age = resource.max_age

        transaction.resource = resource

        return transaction

    def discover(self, transaction):
        """
        Render a GET request to the .well-know/core link.

        :param transaction: the transaction
        :return: the transaction
        """
        transaction.response.code = defines.Codes.CONTENT.number
        payload = ""
        for i in self._parent.root.dump():
            if i == "/":
                continue
            resource = self._parent.root[i]
            if resource.visible:
                ret = self.valid(transaction.request.uri_query, resource.attributes)
                if ret:
                    payload += self.corelinkformat(resource)

        transaction.response.payload = payload
        transaction.response.content_type = defines.Content_types["application/link-format"]
        return transaction

    @staticmethod
    def valid(query, attributes):
        query = query.split("&")
        for q in query:
            q = str(q)
            assert(isinstance(q, str))
            tmp = q.split("=")
            if len(tmp) > 1:
                k = tmp[0]
                v = tmp[1]
                if k in attributes:
                    if v == attributes[k]:
                        continue
                    else:
                        return False
                else:
                    return False
        return True

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
