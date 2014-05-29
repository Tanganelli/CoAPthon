from coapthon2.resources.resource import Resource

__author__ = 'Giacomo Tanganelli'
__version__ = "2.0"


class Hello(Resource):

    def __init__(self, name="HelloResource"):
        super(Hello, self).__init__(name, visible=True, observable=True, allow_children=True)
        self.payload = {"text/plain": "Hello, world!", "application/xml": "HELLO, XML"}

    def new_resource(self):
        return Hello()

    def render_GET(self, query=None):
        return {"Payload": self.payload, "ETag": self.etag, "Max-Age": 30}

    def render_PUT(self, payload=None, query=None):
        return {"Payload": payload, "ETag": self.etag}

    def render_POST(self, payload=None, query=None):
        q = "?" + "&".join(query)
        return {"Payload": payload, "ETag": self.etag, "Location-Path": "pippo/prova/hello3", "Location-Query": q}

    def render_DELETE(self, query=None):
        return True
