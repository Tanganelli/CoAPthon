from coapthon.resources.resource import Resource

__author__ = 'Giacomo Tanganelli'


class RemoteResource(Resource):
    def __init__(self, name, remote_server, remote_path, coap_server=None, visible=True, observable=True, allow_children=True):
        super(RemoteResource, self).__init__(name, coap_server, visible=visible, observable=observable,
                                             allow_children=allow_children)
        self.remote_path = remote_path
        self.remote_server = remote_server
