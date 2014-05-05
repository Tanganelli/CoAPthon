from coapthon2.resources.resource import Resource

__author__ = 'Giacomo Tanganelli'
__version__ = "2.0"


class Hello(Resource):

    def __init__(self, name):
        super(Hello, self).__init__(name, visible=True, observable=True, allow_children=True)

    def render_GET(self):
        return "Hello, world!"

    def render_PUT(self):
        return Hello("hello")


