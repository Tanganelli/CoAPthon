import time
from coapthon2.resources.resource import Resource

__author__ = 'Giacomo Tanganelli'
__version__ = "2.0"


class BasicResource(Resource):
    def __init__(self, name="BasicResource", coap_server=None):
        super(BasicResource, self).__init__(name, coap_server, visible=True,
                                            observable=True, allow_children=True)
        self.payload = "Basic Resource"

    def render_GET(self, request, response):
        return self.payload

    def render_PUT(self, request, response):
        return request.payload

    def render_POST(self, request, response):
        q = "?" + "&".join(request.query)
        res = BasicResource()
        return {"Payload": request.payload, "Location-Query": q, "Resource": res}

    def render_DELETE(self, request, response):
        return True


class Storage(Resource):
    def __init__(self, name="StorageResource", coap_server=None):
        super(Storage, self).__init__(name, coap_server, visible=True, observable=True, allow_children=True)
        self.payload = "Storage Resource for PUT, POST and DELETE"

    def render_GET(self, request, response):
        return self.payload

    def render_POST(self, request, response):
        q = "?" + "&".join(request.query)
        res = Child()
        return {"Payload": request.payload, "Location-Query": q, "Resource": res}


class Child(Resource):
    def __init__(self, name="ChildResource", coap_server=None):
        super(Child, self).__init__(name, coap_server, visible=True, observable=True, allow_children=True)
        self.payload = ""

    def render_GET(self, request, response):
        return self.payload

    def render_PUT(self, request, response):
        self.payload = request.payload
        return self.payload

    def render_POST(self, request, response):
        q = "?" + "&".join(request.query)
        res = Child()
        return {"Payload": request.payload, "Location-Query": q, "Resource": res}

    def render_DELETE(self, request, response):
        return True


class Separate(Resource):

    def __init__(self, name="Separate", coap_server=None):
        super(Separate, self).__init__(name, coap_server, visible=True, observable=True, allow_children=True)
        self.payload = "Separate"

    def render_GET(self, request, response):
        return {"Payload": self.payload, "ETag": self.etag, "Separate": True, "Callback": self.render_GET_separate}

    def render_GET_separate(self, request, response):
        time.sleep(5)
        return {"Payload": self.payload, "ETag": self.etag}
