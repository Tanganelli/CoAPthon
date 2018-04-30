from coapthon.resources.resource import Resource
from databaseManager import DatabaseManager
from coapthon import defines

__author__ = 'Carmelo Aparo'


class LookupRes(Resource):
    def __init__(self, name="rd-lookup/res"):
        super(LookupRes, self).__init__(name, coap_server=None, visible=True, observable=False)
        self.resource_type = "core.rd-lookup-res"
        self.content_type = defines.Content_types["application/link-format"]

    def render_GET_advanced(self, request, response):
        db = DatabaseManager()
        result = db.search(request.uri_query, "res")
        if type(result) is int:
            response.code = result
        else:
            response.code = defines.Codes.CONTENT.number
            response.payload = result
        return self, response
