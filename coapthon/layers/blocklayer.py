import logging
from coapthon import defines
from coapthon.messages.request import Request
from coapthon.messages.response import Response

logger = logging.getLogger(__name__)

__author__ = 'Giacomo Tanganelli'


class BlockItem(object):
    def __init__(self, byte, num, m, size, payload=None, content_type=None):
        """
        Data structure to store Block parameters

        :param byte: the last byte exchanged
        :param num: the num field of the block option
        :param m: the M bit of the block option
        :param size: the size field of the block option
        :param payload: the overall payload received in all blocks
        :param content_type: the content-type of the payload
        """
        self.byte = byte
        self.num = num
        self.m = m
        self.size = size
        self.payload = payload
        self.content_type = content_type


class BlockLayer(object):
    """
    Handle the Blockwise options. Hides all the exchange to both servers and clients.
    """
    def __init__(self):
        self._block1_sent = {}
        self._block2_sent = {}
        self._block1_receive = {}
        self._block2_receive = {}

    def receive_request(self, transaction):
        """
        Handles the Blocks option in a incoming request.

        :type transaction: Transaction
        :param transaction: the transaction that owns the request
        :rtype : Transaction
        :return: the edited transaction
        """
        if transaction.request.block2 is not None:
            host, port = transaction.request.source
            key_token = hash(str(host) + str(port) + str(transaction.request.token))
            num, m, size = transaction.request.block2
            if key_token in self._block2_receive:
                self._block2_receive[key_token].num = num
                self._block2_receive[key_token].size = size
                self._block2_receive[key_token].m = m
                del transaction.request.block2
            else:
                # early negotiation
                byte = 0
                self._block2_receive[key_token] = BlockItem(byte, num, m, size)
                del transaction.request.block2

        elif transaction.request.block1 is not None:
            # POST or PUT
            host, port = transaction.request.source
            key_token = hash(str(host) + str(port) + str(transaction.request.token))
            num, m, size = transaction.request.block1
            if key_token in self._block1_receive:
                content_type = transaction.request.content_type
                if num != self._block1_receive[key_token].num \
                        or content_type != self._block1_receive[key_token].content_type:
                    # Error Incomplete
                    return self.incomplete(transaction)
                self._block1_receive[key_token].payload += transaction.request.payload
            else:
                # first block
                if num != 0:
                    # Error Incomplete
                    return self.incomplete(transaction)
                content_type = transaction.request.content_type
                self._block1_receive[key_token] = BlockItem(size, num, m, size, transaction.request.payload,
                                                            content_type)

            if m == 0:
                transaction.request.payload = self._block1_receive[key_token].payload
                # end of blockwise
                del transaction.request.block1
                transaction.block_transfer = False
                del self._block1_receive[key_token]
                return transaction
            else:
                # Continue
                transaction.block_transfer = True
                transaction.response = Response()
                transaction.response.destination = transaction.request.source
                transaction.response.token = transaction.request.token
                transaction.response.code = defines.Codes.CONTINUE.number
                transaction.response.block1 = (num, m, size)

            num += 1
            byte = size
            self._block1_receive[key_token].byte = byte
            self._block1_receive[key_token].num = num
            self._block1_receive[key_token].size = size
            self._block1_receive[key_token].m = m

        return transaction

    def receive_response(self, transaction):
        """
        Handles the Blocks option in a incoming response.

        :type transaction: Transaction
        :param transaction: the transaction that owns the response
        :rtype : Transaction
        :return: the edited transaction
        """
        host, port = transaction.response.source
        key_token = hash(str(host) + str(port) + str(transaction.response.token))
        if key_token in self._block1_sent and transaction.response.block1 is not None:
            item = self._block1_sent[key_token]
            transaction.block_transfer = True
            if item.m == 0:
                transaction.block_transfer = False
                del transaction.request.block1
                return transaction
            n_num, n_m, n_size = transaction.response.block1
            if n_num != item.num:  # pragma: no cover
                logger.warning("Blockwise num acknowledged error, expected " + str(item.num) + " received " +
                               str(n_num))
                return None
            if n_size < item.size:
                logger.debug("Scale down size, was " + str(item.size) + " become " + str(n_size))
                item.size = n_size
            request = transaction.request
            del request.mid
            del request.block1
            request.payload = item.payload[item.byte: item.byte+item.size]
            item.num += 1
            item.byte += item.size
            if len(item.payload) <= item.byte:
                item.m = 0
            else:
                itme.m = 1
            request.block1 = (item.num, item.m, item.size)
        elif transaction.response.block2 is not None:

            num, m, size = transaction.response.block2
            if m == 1:
                transaction.block_transfer = True
                if key_token in self._block2_sent:
                    item = self._block2_sent[key_token]
                    if num != item.num:  # pragma: no cover
                        logger.error("Receive unwanted block")
                        return self.error(transaction, defines.Codes.REQUEST_ENTITY_INCOMPLETE.number)
                    if item.content_type is None:
                        item.content_type = transaction.response.content_type
                    if item.content_type != transaction.response.content_type:  # pragma: no cover
                        logger.error("Content-type Error")
                        return self.error(transaction, defines.Codes.UNSUPPORTED_CONTENT_FORMAT.number)
                    item.byte += size
                    item.num = num + 1
                    item.size = size
                    item.m = m
                    item.payload += transaction.response.payload
                else:
                    item = BlockItem(size, num + 1, m, size, transaction.response.payload,
                                     transaction.response.content_type)
                    self._block2_sent[key_token] = item
                request = transaction.request
                del request.mid
                del request.block2
                request.block2 = (item.num, 0, item.size)
            else:
                transaction.block_transfer = False
                if key_token in self._block2_sent:
                    if self._block2_sent[key_token].content_type != transaction.response.content_type:  # pragma: no cover
                        logger.error("Content-type Error")
                        return self.error(transaction, defines.Codes.UNSUPPORTED_CONTENT_FORMAT.number)
                    transaction.response.payload = self._block2_sent[key_token].payload + transaction.response.payload
                    del self._block2_sent[key_token]
        else:
            transaction.block_transfer = False
        return transaction

    def receive_empty(self, empty, transaction):
        """
        Dummy function. Used to do not broke the layered architecture.

        :type empty: Message
        :param empty: the received empty message
        :type transaction: Transaction
        :param transaction: the transaction that owns the empty message
        :rtype : Transaction
        :return: the transaction
        """
        return transaction

    def send_response(self, transaction):
        """
        Handles the Blocks option in a outgoing response.

        :type transaction: Transaction
        :param transaction: the transaction that owns the response
        :rtype : Transaction
        :return: the edited transaction
        """
        host, port = transaction.request.source
        key_token = hash(str(host) + str(port) + str(transaction.request.token))
        if (key_token in self._block2_receive and transaction.response.payload is not None) or \
                (transaction.response.payload is not None and len(transaction.response.payload) > defines.MAX_PAYLOAD):
            if key_token in self._block2_receive:

                byte = self._block2_receive[key_token].byte
                size = self._block2_receive[key_token].size
                num = self._block2_receive[key_token].num

            else:
                byte = 0
                num = 0
                size = defines.MAX_PAYLOAD
                m = 1

                self._block2_receive[key_token] = BlockItem(byte, num, m, size)

            if len(transaction.response.payload) > (byte + size):
                m = 1
            else:
                m = 0
            transaction.response.payload = transaction.response.payload[byte:byte + size]
            del transaction.response.block2
            transaction.response.block2 = (num, m, size)

            self._block2_receive[key_token].byte += size
            self._block2_receive[key_token].num += 1
            if m == 0:
                del self._block2_receive[key_token]

        return transaction

    def send_request(self, request):
        """
        Handles the Blocks option in a outgoing request.

        :type request: Request
        :param request: the outgoing request
        :return: the edited request
        """
        assert isinstance(request, Request)
        if request.block1 or (request.payload is not None and len(request.payload) > defines.MAX_PAYLOAD):
            host, port = request.destination
            key_token = hash(str(host) + str(port) + str(request.token))
            if request.block1:
                num, m, size = request.block1
            else:
                num = 0
                m = 1
                size = defines.MAX_PAYLOAD

            self._block1_sent[key_token] = BlockItem(size, num, m, size, request.payload, request.content_type)
            request.payload = request.payload[0:size]
            del request.block1
            request.block1 = (num, m, size)
        elif request.block2:
            host, port = request.destination
            key_token = hash(str(host) + str(port) + str(request.token))
            num, m, size = request.block2
            item = BlockItem(size, num, m, size, "", None)
            self._block2_sent[key_token] = item
            return request
        return request

    @staticmethod
    def incomplete(transaction):
        """
        Notifies incomplete blockwise exchange.

        :type transaction: Transaction
        :param transaction: the transaction that owns the response
        :rtype : Transaction
        :return: the edited transaction
        """
        transaction.block_transfer = True
        transaction.response = Response()
        transaction.response.destination = transaction.request.source
        transaction.response.token = transaction.request.token
        transaction.response.code = defines.Codes.REQUEST_ENTITY_INCOMPLETE.number
        return transaction

    @staticmethod
    def error(transaction, code):  # pragma: no cover
        """
        Notifies generic error on blockwise exchange.

        :type transaction: Transaction
        :param transaction: the transaction that owns the response
        :rtype : Transaction
        :return: the edited transaction
        """
        transaction.block_transfer = True
        transaction.response = Response()
        transaction.response.destination = transaction.request.source
        transaction.response.type = defines.Types["RST"]
        transaction.response.token = transaction.request.token
        transaction.response.code = code
        return transaction

