from coapthon.resources.resource import Resource
from databaseManager import DatabaseManager
from coapthon import defines

__author__ = 'Carmelo Aparo'


class Registration(Resource):
    """
    Implementation of the registration resource.
    """
    def __init__(self, name="rd"):
        """
        Initialize a resource for registration management.
        :param name: the name of the resource.
        """
        super(Registration, self).__init__(name, coap_server=None, visible=True, observable=False)
        self.resource_type = "core.rd"
        self.content_type = "application/link-format"

    def render_GET_advanced(self, request, response):
        """
        Method GET to read endpoint links.
        :param request: the request of the GET message.
        :param response: the response to the GET request.
        :return: the response to the GET request.
        """
        if request.uri_path == 'rd':
            raise NotImplementedError
        if (request.accept != defines.Content_types["application/link-format"]) and (request.accept is not None):
            response.code = defines.Codes.NOT_ACCEPTABLE.number
            return self, response
        res = "res=" + request.uri_path
        db = DatabaseManager()
        result = db.search(res, "res")
        if type(result) is int:
            response.code = result
        else:
            response.code = defines.Codes.CONTENT.number
            response.payload = result
            response.content_type = defines.Content_types["application/link-format"]
        return self, response

    def render_POST_advanced(self, request, response):
        """
        Method POST to register and update an endpoint.
        :param request: the request of the POST message.
        :param response: the response to the POST message.
        :return: the response to the POST message.
        """
        db = DatabaseManager()
        if request.uri_path == 'rd':
            if request.content_type != defines.Content_types["application/link-format"]:
                response.code = defines.Codes.BAD_REQUEST.number
                return self, response
            uri_query = request.uri_query
            if "con=" not in uri_query:
                uri_query += "&con=coap://" + request.source[0] + ":" + str(request.source[1])
            result = db.insert(uri_query, request.payload)
            if type(result) is int:
                response.code = result
            else:
                response.location_path = result
                response.code = defines.Codes.CREATED.number
        else:
            response.code = db.update(request.uri_path, request.uri_query)
        return self, response

    def render_DELETE_advanced(self, request, response):
        """
        Method DELETE to delete an endpoint registration.
        :param request: the request of the DELETE message.
        :param response: the response to the DELETE message.
        :return: the response to the DELETE message.
        """
        if request.uri_path == 'rd':
            raise NotImplementedError
        db = DatabaseManager()
        response.code = db.delete(request.uri_path)
        return False, response
