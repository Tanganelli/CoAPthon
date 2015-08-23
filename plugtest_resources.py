from coapthon.resources.resource import Resource

__author__ = 'Giacomo Tanganelli'
__version__ = "2.0"


class TestResource(Resource):
    def __init__(self, name="TestResource", coap_server=None):
        super(TestResource, self).__init__(name, coap_server, visible=True, observable=False, allow_children=True)
        self.payload = "Test Resource"

    def render_GET(self, request):
        return self

    def render_PUT(self, request):
        self.payload = request.payload
        return self

    def render_POST(self, request):
        res = TestResource()
        res.location_query = request.query
        res.payload = request.payload
        return res

    def render_DELETE(self, request):
        return True