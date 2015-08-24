import time
from coapthon import defines
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
        for option in request.options:
            if option.number == defines.inv_options["Content-Type"]:
                self.payload = {option.value: request.payload}
                return self
        self.payload = request.payload
        return self

    def render_POST(self, request):
        res = TestResource()
        res.location_query = request.query
        for option in request.options:
            if option.number == defines.inv_options["Content-Type"]:
                res.payload = {option.value: request.payload}
                return res
        res.payload = request.payload
        return res

    def render_DELETE(self, request):
        return True


class SeparateResource(Resource):

    def __init__(self, name="Separate", coap_server=None):
        super(SeparateResource, self).__init__(name, coap_server, visible=True, observable=False, allow_children=False)
        self.payload = "Separate Resource"

    def render_GET(self, request):
        return self, self.render_GET_separate

    def render_GET_separate(self, request):
        time.sleep(5)
        return self