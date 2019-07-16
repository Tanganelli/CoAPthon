from coapthon.resources.resource import Resource
from databaseManager import DatabaseManager
from coapthon import defines

__author__ = 'Carmelo Aparo'


class LookupRes(Resource):
    """
    Implementation of the resource lookup resource.
    """
    def __init__(self, name="rd-lookup/res"):
        """
        Initialize a resource for resource lookup.
        :param name: the name of the resource.
        """
        super(LookupRes, self).__init__(name, coap_server=None, visible=True, observable=False)
        self.resource_type = "core.rd-lookup-res"
        self.content_type = "application/link-format"

    def render_GET_advanced(self, request, response):
        """
        Method GET to search resource links.
        :param request: the request of the GET message.
        :param response: the response to the GET request.
        :return: the response to the GET request.
        """
        if (request.accept != defines.Content_types["application/link-format"]) and (request.accept is not None):
            response.code = defines.Codes.NOT_ACCEPTABLE.number
            return self, response
        db = DatabaseManager()
        result = db.search(request.uri_query, "res")
        if type(result) is int:
            response.code = result
        else:
            response.code = defines.Codes.CONTENT.number
            response.payload = result
            response.content_type = defines.Content_types["application/link-format"]
        return self, response
