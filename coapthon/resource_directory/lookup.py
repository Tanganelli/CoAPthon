from coapthon.resources.resource import Resource
from databaseManager import DatabaseManager
from coapthon import defines

__author__ = 'Carmelo Aparo'


class Lookup(Resource):
    def __init__(self, name="rd"):
        super(Lookup, self).__init__(name)

    def render_GET_advanced(self, request, response):
        db = DatabaseManager()
        if request.uri_path == 'rd-lookup/ep':
            result = db.search(request.uri_query, "ep")
        elif request.uri_path == 'rd-lookup/res':
            result = db.search(request.uri_query, "res")
        if type(result) is int:
            response.code = result
        else:
            response.code = defines.Codes.CONTENT.number
            response.payload = result
        return self, response
