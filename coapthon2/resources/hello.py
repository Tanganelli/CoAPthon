import time
from coapthon2.resources.resource import Resource

__author__ = 'Giacomo Tanganelli'
__version__ = "2.0"


class Hello(Resource):

    def __init__(self, name="HelloResource"):
        super(Hello, self).__init__(name, visible=True, observable=True, allow_children=True)
        self.payload = {"text/plain": "Hello, world!", "application/xml": "HELLO, XML"}

    def render_GET(self, query=None):
        return {"Payload": self.payload, "ETag": self.etag, "Separate": True, "Callback": self.render_GET_separate}
        #time.sleep(5)
        #return {"Payload": self.payload, "ETag": self.etag}

    def render_GET_separate(self, query=None):
        time.sleep(5)
        return {"Payload": self.payload, "ETag": self.etag}

    def render_PUT(self, payload=None, query=None):
        return {"Payload": payload, "ETag": "PLUTO"}

    def render_POST(self, payload=None, query=None):
        q = "?" + "&".join(query)
        res = Hello(self._server)
        return {"Payload": payload, "ETag": "PIPPO", "Location-Query": q, "Resource": res}

    def render_DELETE(self, query=None):
        return True
