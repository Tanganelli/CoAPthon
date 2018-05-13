from coapthon.resources.resource import Resource

__author__ = 'Carmelo Aparo'


class Lookup(Resource):
    """
    Implementation of a lookup resource.
    """
    def __init__(self, name="rd-lookup"):
        """
        Initialize a resource not visible.
        :param name: the name of the resource.
        """
        super(Lookup, self).__init__(name, coap_server=None, visible=False, observable=False)
