from coapthon2.resources.resource import Resource

__author__ = 'Giacomo Tanganelli'
__version__ = "2.0"


class Hello(Resource):

    def __init__(self, name):
        super(Hello, self).__init__(name, visible=True, observable=True, allow_children=True)
        self.payload = {"text/plain": "Hello, world!"}

    def render_GET(self, query=None):
        return self.payload

    def render_PUT(self, create=True, payload=None, query=None):
        if not create:
            self.payload = payload
            return self
        else:
            new = Hello("hello")
            new.payload = payload
            return new

