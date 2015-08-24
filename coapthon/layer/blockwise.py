import struct
from coapthon import defines
from coapthon.utils import byte_len, bit_len

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
        for option in request.options:
            if option.number == defines.inv_options["Block2"]:
                host, port = request.source
                key = hash(str(host) + str(port) + str(request.token))
                num, m, size = self.parse_blockwise(option.raw_value)
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
                num, m, size = self.parse_blockwise(option.raw_value)
                # remember choices
                self._parent.blockwise[key] = (1, 0, num, m, size)
        return True, request

    def start_block2(self, request):
        """
        Initialize a blockwise response. Used if payload > 1024
        :param request: the request message
        """
        host, port = request.source
        key = hash(str(host) + str(port) + str(request.token))
        self._parent.blockwise[key] = (2, 0, 0, 1, 6)  # 6 == 2^10 = 1024

    def handle_response(self, key, response, resource):
        """
        Handle Blockwise in responses.
        :param key: key parameter to search inside the disctionary
        :param response: the response message
        :param resource: the request message
        :return: the new response
        """
        block, byte, num, m, size = self._parent.blockwise[key]
        payload = resource.payload
        if block == 2:
            ret = payload[byte:byte + (pow(2, (size + 4)))]

            if len(ret) == pow(2, (size + 4)):
                m = 1
            else:
                m = 0
            response.block2 = (num, m, size)
            response.payload = ret
            byte += (pow(2, (size + 4)))
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

    @staticmethod
    def parse_blockwise(value):
        """
        Parse Blockwise option.
        :param value: option value
        :return: num, m, size
        """

        length = byte_len(value)
        if length == 1:
            num = value & 0xF0
            num >>= 4
            m = value & 0x08
            m >>= 3
            size = value & 0x07
        elif length == 2:
            num = value & 0xFFF0
            num >>= 4
            m = value & 0x0008
            m >>= 3
            size = value & 0x0007
        else:
            num = value & 0xFFFFF0
            num >>= 4
            m = value & 0x000008
            m >>= 3
            size = value & 0x000007
        return num, int(m), size