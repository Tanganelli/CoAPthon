from coapthon.messages.response import Response
from coapthon import defines

__author__ = 'Giacomo Tanganelli'


class RequestLayer(object):
    """
    Class to handle the Request/Response layer
    """
    def __init__(self, server):
        self._server = server

    def receive_request(self, transaction):
        """
        Handle request and execute the requested method

        :type transaction: Transaction
        :param transaction: the transaction that owns the request
        :rtype : Transaction
        :return: the edited transaction with the response to the request
        """
        method = transaction.request.code
        if method == defines.Codes.GET.number:
            transaction = self._handle_get(transaction)
        elif method == defines.Codes.POST.number:
            transaction = self._handle_post(transaction)
        elif method == defines.Codes.PUT.number:
            transaction = self._handle_put(transaction)
        elif method == defines.Codes.DELETE.number:
            transaction = self._handle_delete(transaction)
        elif method == defines.Codes.FETCH.number:
            transaction = self._handle_fetch(transaction)
        elif method == defines.Codes.PATCH.number:
            transaction = self._handle_patch(transaction)
        else:
            transaction.response = None
        return transaction

    def send_request(self, request):
        """
         Dummy function. Used to do not broke the layered architecture.

        :type request: Request
        :param request: the request
        :return: the request unmodified
        """
        return request

    def _handle_get(self, transaction):
        """
        Handle GET requests

        :type transaction: Transaction
        :param transaction: the transaction that owns the request
        :rtype : Transaction
        :return: the edited transaction with the response to the request
        """
        path = str("/" + transaction.request.uri_path)
        transaction.response = Response()
        transaction.response.destination = transaction.request.source
        transaction.response.token = transaction.request.token
        if path == defines.DISCOVERY_URL:
            transaction = self._server.resourceLayer.discover(transaction)
        else:
            try:
                resource = self._server.root[path]
            except KeyError:
                resource = None
            if resource is None or path == '/':
                # Not Found
                transaction.response.code = defines.Codes.NOT_FOUND.number
            else:
                transaction.resource = resource
                transaction = self._server.resourceLayer.get_resource(transaction)
        return transaction

    def _handle_put(self, transaction):
        """
        Handle PUT requests

        :type transaction: Transaction
        :param transaction: the transaction that owns the request
        :rtype : Transaction
        :return: the edited transaction with the response to the request
        """
        path = str("/" + transaction.request.uri_path)
        transaction.response = Response()
        transaction.response.destination = transaction.request.source
        transaction.response.token = transaction.request.token
        try:
            resource = self._server.root[path]
        except KeyError:
            resource = None
        if resource is None:
            transaction.response.code = defines.Codes.NOT_FOUND.number
        else:
            transaction.resource = resource
            # Update request
            transaction = self._server.resourceLayer.update_resource(transaction)
        return transaction

    def _handle_post(self, transaction):
        """
        Handle POST requests

        :type transaction: Transaction
        :param transaction: the transaction that owns the request
        :rtype : Transaction
        :return: the edited transaction with the response to the request
        """
        path = str("/" + transaction.request.uri_path)
        transaction.response = Response()
        transaction.response.destination = transaction.request.source
        transaction.response.token = transaction.request.token

        # Create request
        transaction = self._server.resourceLayer.create_resource(path, transaction)
        return transaction

    def _handle_delete(self, transaction):
        """
        Handle DELETE requests

        :type transaction: Transaction
        :param transaction: the transaction that owns the request
        :rtype : Transaction
        :return: the edited transaction with the response to the request
        """
        path = str("/" + transaction.request.uri_path)
        transaction.response = Response()
        transaction.response.destination = transaction.request.source
        transaction.response.token = transaction.request.token
        try:
            resource = self._server.root[path]
        except KeyError:
            resource = None

        if resource is None:
            transaction.response.code = defines.Codes.NOT_FOUND.number
        else:
            # Delete
            transaction.resource = resource
            transaction = self._server.resourceLayer.delete_resource(transaction, path)
        return transaction

    def _handle_fetch(self, transaction):
        """
                Handle FETCH requests

                :type transaction: Transaction
                :param transaction: the transaction that owns the request
                :rtype : Transaction
                :return: the edited transaction with the response to the request
                """
        path = str("/" + transaction.request.uri_path)
        transaction.response = Response()
        transaction.response.destination = transaction.request.source
        transaction.response.token = transaction.request.token
        print "FETCH IN CORSO"
        if path == defines.DISCOVERY_URL:
            transaction = self._server.resourceLayer.discover(transaction)
        else:
            try:
                resource = self._server.root[path]
            except KeyError:
                resource = None
            if resource is None or path == '/':
                # Not Found
                transaction.response.code = defines.Codes.NOT_FOUND.number
            else:
                transaction.resource = resource
                transaction = self._server.resourceLayer.fetch_resource(transaction)

        return transaction

    def _handle_patch(self, transaction):
        """
        Handle PATCH requests

        :type transaction: Transaction
        :param transaction: the transaction that owns the request
        :rtype : Transaction
        :return: the edited transaction with the response to the request
        """
        path = str("/" + transaction.request.uri_path)
        transaction.response = Response()
        transaction.response.destination = transaction.request.source
        transaction.response.token = transaction.request.token
        print "PATCH IN CORSO"
        try:
            resource = self._server.root[path]
        except KeyError:
            resource = None
        if resource is None:
            transaction.response.code = defines.Codes.NOT_FOUND.number
        else:
            transaction.resource = resource
            # Update request
            transaction = self._server.resourceLayer.patch_resource(transaction)
        return transaction
