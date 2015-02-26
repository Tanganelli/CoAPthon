from coapthon2 import defines

__author__ = 'Giacomo Tanganelli'
__version__ = "2.0"


class BlockwiseLayer(object):
    """
    Handles the Blockwise feature.
    """
    def __init__(self, parent):
        """
        Initialize a Blockwise Layer.

        :type parent: coapserver.CoAP
        :param parent: the CoAP server
        """
        self._parent = parent

    def handle_request(self, request):
        for option in request.options:
            if option.number == defines.inv_options["Block2"]:
                host, port = request.source
                key = hash(str(host) + str(port) + str(request.token))
                # remember choices
                self._parent.blockwise[key] = option.raw_value
        return True, request