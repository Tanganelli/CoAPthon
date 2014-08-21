import time
from coapthon2.resources.resource import Resource

__author__ = 'Giacomo Tanganelli'
__version__ = "2.0"


class Storage(Resource):
    def __init__(self, name="StorageResource"):
        super(Storage, self).__init__(name, visible=True, observable=True, allow_children=True)
        self.payload = "Storage Resource for PUT, POST and DELETE"

    def render_GET(self, request, query=None):
        return self.payload

    def render_POST(self, request, payload=None, query=None):
        q = "?" + "&".join(query)
        res = Child()
        return {"Payload": payload, "Location-Query": q, "Resource": res}


class Child(Resource):
    def __init__(self, name="ChildResource"):
        super(Child, self).__init__(name, visible=True, observable=True, allow_children=True)
        self.payload = ""

    def render_GET(self, request, query=None):
        return self.payload

    def render_PUT(self, request, payload=None, query=None):
        return payload

    def render_POST(self, request, payload=None, query=None):
        q = "?" + "&".join(query)
        res = Child()
        return {"Payload": payload, "Location-Query": q, "Resource": res}

    def render_DELETE(self, request, query=None):
        return True


class Separate(Resource):

    def __init__(self, name="Separate"):
        super(Separate, self).__init__(name, visible=True, observable=True, allow_children=True)
        self.payload = "Separate"

    def render_GET(self, request, query=None):
        return {"Payload": self.payload, "ETag": self.etag, "Separate": True, "Callback": self.render_GET_separate}

    def render_GET_separate(self, request, query=None):
        time.sleep(5)
        return {"Payload": self.payload, "ETag": self.etag}
