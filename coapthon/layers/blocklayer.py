import logging
from coapthon import defines
from coapthon.messages.request import Request
from coapthon.messages.response import Response

logger = logging.getLogger(__name__)


class BlockItem(object):
    def __init__(self, byte, num, m, size, payload=None, content_type=None):
        self.byte = byte
        self.num = num
        self.m = m
        self.size = size
        self.payload = payload
        self.content_type = content_type


class BlockLayer(object):
    def __init__(self):
        self._block1_sent = {}
        self._block2_sent = {}
        self._block1_receive = {}
        self._block2_receive = {}

    def receive_request(self, transaction):
        """

        :type transaction: Transaction
        :param transaction:
        :rtype : Transaction
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
                    transaction.block_transfer = True
                    transaction.response = Response()
                    transaction.response.destination = transaction.request.source
                    transaction.response.token = transaction.request.token
                    transaction.response.code = defines.Codes.REQUEST_ENTITY_INCOMPLETE.number
                    return transaction
                self._block1_receive[key_token].payload += transaction.request.payload
            else:
                # first block
                if num != 0:
                    # Error Incomplete
                    transaction.block_transfer = True
                    transaction.response = Response()
                    transaction.response.destination = transaction.request.source
                    transaction.response.token = transaction.request.token
                    transaction.response.code = defines.Codes.REQUEST_ENTITY_INCOMPLETE.number
                    return transaction
                content_type = transaction.request.content_type
                self._block1_receive[key_token] = BlockItem(size, num, m, size, transaction.request.payload,
                                                            content_type)

            if m == 0:
                transaction.request.payload = self._block1_receive[key_token].payload
                # end of blockwise
                del transaction.request.block1
                transaction.block_transfer = False
                # TODO remove from _block1_receive
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

        :type transaction: Transaction
        :param transaction:
        :rtype : Transaction
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
            if n_num != item.num:
                logger.warning("Blockwise num acknowledged error, expected " + str(item.num) + " received " + str(n_num))
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
                m = 0
            else:
                m = 1
            request.block1 = (item.num, m, item.size)
        elif transaction.response.block2 is not None:

            num, m, size = transaction.response.block2
            if m == 1:
                transaction.block_transfer = True
                if key_token in self._block2_sent:
                    item = self._block2_sent[key_token]
                    if num != item.num:
                        logger.error("Receive unwanted block")
                        # TODO send rst
                        return None
                    if item.content_type is None:
                        item.content_type = transaction.response.content_type
                    if item.content_type != transaction.response.content_type:
                        logger.error("Content-type Error")
                        # TODO send rst
                        return None
                    item.byte += size
                    item.num = num
                    item.size = size
                    item.m = m
                    item.payload += transaction.response.payload
                else:
                    item = BlockItem(size, num, m, size, transaction.response.payload,
                                     transaction.response.content_type)
                    self._block2_sent[key_token] = item
                request = transaction.request
                del request.mid
                del request.block2
                request.block2 = (item.num + 1, 0, item.size)
            else:
                transaction.block_transfer = False
                if key_token in self._block2_sent:
                    if self._block2_sent[key_token].content_type != transaction.response.content_type:
                        logger.error("Content-type Error")
                        # TODO send rst
                        return None
                    transaction.response.payload = self._block2_sent[key_token].payload + transaction.response.payload
                del self._block2_sent[key_token]
        else:
            transaction.block_transfer = False
        return transaction

    def receive_empty(self, empty, transaction):
        """

        :type empty: Message
        :param empty:
        :type transaction: Transaction
        :param transaction:
        :rtype : Transaction
        """
        return transaction

    def send_empty(self, message):
        """

        :type transaction: Transaction
        :param transaction:
        :type message: Message
        :param message:
        """
        return message

    def send_response(self, transaction):
        """

        :type transaction: Transaction
        :param transaction:
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

            ret = transaction.response.payload[byte:byte + size]
            if len(ret) == size:
                m = 1
            else:
                m = 0
            transaction.response.payload = transaction.response.payload[byte:byte + size]
            del transaction.response.block2
            transaction.response.block2 = (num, m, size)

            self._block2_receive[key_token].byte += size
            self._block2_receive[key_token].num += 1
            if m == 0:
                # TODO remove from _block2_receive
                # del self._block2_receive[key_token]
                pass

        return transaction

    def send_request(self, request):
        """

        :type request: Request
        :param request:
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
            # TODO check that the payload inside the dict doesn't change
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


