from coapthon.resources.resource import Resource
from databaseManager import DatabaseManager
from coapthon import defines

__author__ = 'Carmelo Aparo'


class Registration(Resource):
    def __init__(self, name="rd"):
        super(Registration, self).__init__(name)

    def render_GET_advanced(self, request, response):
        if request.uri_path == 'rd':
            raise NotImplementedError
        res = "res=/" + request.uri_path
        db = DatabaseManager()
        result = db.search(res, "res")
        if (type(result) is unicode) or (type(result) is str):
            response.code = defines.Codes.CONTENT.number
            response.payload = result
        else:
            response.code = result
        return self, response

    def render_POST_advanced(self, request, response):
        db = DatabaseManager()
        if request.uri_path == 'rd':
            result = db.insert(request.uri_query, request.payload)
            if type(result) is str:
                response.location_path = result
                response.code = defines.Codes.CREATED.number
            else:
                response.code = result
        else:
            response.code = db.update("/" + request.uri_path, request.uri_query)
        return self, response

    def render_DELETE_advanced(self, request, response):
        if request.uri_path == 'rd':
            raise NotImplementedError
        db = DatabaseManager()
        response.code = db.delete("/" + request.uri_path)
        return True, response
