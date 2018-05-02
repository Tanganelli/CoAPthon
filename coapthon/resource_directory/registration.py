from coapthon.resources.resource import Resource
from databaseManager import DatabaseManager
from coapthon import defines

__author__ = 'Carmelo Aparo'


class Registration(Resource):
    def __init__(self, name="rd"):
        super(Registration, self).__init__(name, coap_server=None, visible=True, observable=False)
        self.resource_type = "core.rd"
        self.content_type = defines.Content_types["application/link-format"]

    def render_GET_advanced(self, request, response):
        if request.uri_path == 'rd':
            raise NotImplementedError
        if (request.accept != defines.Content_types["application/link-format"]) and (request.accept is not None):
            response.code = defines.Codes.NOT_ACCEPTABLE.number
            return self, response
        res = "res=/" + request.uri_path
        db = DatabaseManager()
        result = db.search(res, "res")
        if type(result) is int:
            response.code = result
        else:
            response.code = defines.Codes.CONTENT.number
            response.payload = result
            response.actual_content_type = defines.Content_types["application/link-format"]
        return self, response

    def render_POST_advanced(self, request, response):
        db = DatabaseManager()
        if request.uri_path == 'rd':
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
            response.code = db.update("/" + request.uri_path, request.uri_query)
        return self, response

    def render_DELETE_advanced(self, request, response):
        if request.uri_path == 'rd':
            raise NotImplementedError
        db = DatabaseManager()
        response.code = db.delete("/" + request.uri_path)
        return False, response
