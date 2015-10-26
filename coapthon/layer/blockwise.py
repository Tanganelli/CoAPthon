import struct
from coapthon import defines
from coapthon.utils import byte_len, bit_len, parse_blockwise

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
        """
        Store Blockwise parameter required by clients

        :param request: the request message
        :return: M bit, request
        """
        ret = True
        for option in request.options:
            if option.number == defines.inv_options["Block2"]:
                host, port = request.source
                key = hash(str(host) + str(port) + str(request.token))
                num, m, size = parse_blockwise(option.raw_value)
                # remember choices
                if key in self._parent.blockwise:
                    block, byte, num2, m2, size2 = self._parent.blockwise[key]
                    if block == 2:
                        self._parent.blockwise[key] = (2, byte, num, m, size)
                    else:
                        self._parent.blockwise[key] = (2, 0, num, m, size)
                else:
                    self._parent.blockwise[key] = (2, 0, num, m, size)
            elif option.number == defines.inv_options["Block1"]:
                host, port = request.source
                key = hash(str(host) + str(port) + str(request.token))
                num, m, size = parse_blockwise(option.raw_value)
                # remember choices
                self._parent.blockwise[key] = (1, 0, num, m, size)
                if m == 0:
                    del self._parent.blockwise[key]
                    ret = False
        return ret, request

    def start_block2(self, request):
        """
        Initialize a blockwise response. Used if payload > 1024

        :param request: the request message
        """
        host, port = request.source
        key = hash(str(host) + str(port) + str(request.token))
        self._parent.blockwise[key] = (2, 0, 0, 1, 1024)

    def handle_response(self, key, response, resource):
        """
        Handle Blockwise in responses.

        :param key: key parameter to search inside the dictionary
        :param response: the response message
        :param resource: the request message
        :return: the new response
        """
        block, byte, num, m, size = self._parent.blockwise[key]
        payload = resource.payload
        if block == 2:
            ret = payload[byte:byte + size]

            if len(ret) == size:
                m = 1
            else:
                m = 0
            response.block2 = (num, m, size)
            response.payload = ret
            byte += size
            num += 1
            if m == 0:
                del self._parent.blockwise[key]
            else:
                self._parent.blockwise[key] = (2, byte, num, m, size)

        elif block == 1:
            if m == 1:
                response.code = defines.responses["CONTINUE"]
            response.block1 = (num, m, size)
        return response


