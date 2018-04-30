from coapthon.resources.resource import Resource

__author__ = 'Carmelo Aparo'


class Lookup(Resource):
    def __init__(self, name="rd-lookup"):
        super(Lookup, self).__init__(name, coap_server=None, visible=False, observable=False)
