import time
from coapthon import defines
from coapthon.messages.message import Message

__author__ = 'Giacomo Tanganelli'
__version__ = "2.0"


class MessageLayer(object):
    """
    Handles message functionality: Acknowledgment, Reset.
    """
    def __init__(self, parent):
        """
        Initialize a Message Layer.

        :type parent: coapserver.CoAP
        :param parent: the CoAP server
        """
        self._parent = parent

    @staticmethod
    def reliability_response(request, response):
        """
        Sets Message type according to the request

        :param request: the request object
        :param response: the response object
        :return: the response
        """
        if not (response.type == defines.inv_types['ACK'] or response.type == defines.inv_types['RST']):
            if request.type == defines.inv_types['CON']:
                if request.acknowledged:
                    response.type = defines.inv_types['CON']
                else:
                    request.acknowledged = True
                    response.type = defines.inv_types['ACK']
                    response.mid = request.mid
            else:
                response.type = defines.inv_types['NON']
        else:
            response.mid = request.mid

        return response

    def matcher_response(self, response):
        """
        Sets MID if not already set. Save the sent message for acknowledge and duplication handling.

        :param response: the response
        :return: the response
        :raise AttributeError: if the message destination is not properly set.
        """
        if response.mid is None:
            response.mid = self._parent.current_mid % (1 << 16)
            self._parent.current_mid += 1
        host, port = response.destination
        if host is None:
            raise AttributeError("Response has no destination address set")
        if port is None or port == 0:
            raise AttributeError("Response has no destination port set")
        key = hash(str(host) + str(port) + str(response.mid))
        self._parent.sent[key] = (response, time.time())
        return response

    def handle_message(self, message):
        """
        Handles ACK and RST. Handles mapping with the response previously sent and verify if an Observing relation
        must be deleted.

        :param message: the message received
        """
        try:
            host, port = message.source
        except AttributeError:
            return
        key = hash(str(host) + str(port) + str(message.mid))

        t = self._parent.sent.get(key)
        if t is None:
            # log.err(defines.types[message.type] + " received without the corresponding message")
            return
        response, timestamp = t
        # Reliability
        if message.type == defines.inv_types['ACK']:
            response.acknowledged = True
        elif message.type == defines.inv_types['RST']:
            response.rejected = True

        # Observing
        if message.type == defines.inv_types['RST']:
            for resource in self._parent.relation.keys():
                host, port = message.source
                key = hash(str(host) + str(port) + str(response.token))
                observers = self._parent.relation.get(resource)
                if observers is not None:
                    del observers[key]
                    log.msg("Cancel observing relation")
                    if len(observers) == 0:
                        del self._parent.relation[resource]

        # cancel retransmission
        # log.msg("Cancel retrasmission to:" + host + ":" + str(port))
        try:
            call_id, retrasmission_count = self._parent.call_id.get(key)
            if call_id is not None:
                call_id.cancel()
        except:
            pass
        self._parent.sent[key] = (response, time.time())

    def start_separate_timer(self, request):
        """
        Start separate Timer.

        :param request: the request
        :return: the timer object
        """
        t = self._parent.executor.submit(self.send_ack, [request, defines.SEPARATE_TIMEOUT])
        return t

    @staticmethod
    def stop_separate_timer(timer):
        """
        Stop separate timer.

        :param timer: the timer object
        :return: True
        """
        timer.cancel()
        return True

    def send_separate(self, request):
        """
        Send separate acknowledgement, if required.

        :param request: the request
        """
        if request.type == defines.inv_types["CON"]:
            self.send_ack(request)

    def send_ack(self, request):
        # Handle separate
        """
        Sends an ACK message for the request.

        :param request: [request] or request
        """
        if isinstance(request, list):
            if len(request) == 2:
                time.sleep(request[1])
            request = request[0]
        ack = Message.new_ack(request)
        host, port = request.source
        if not request.acknowledged:
            self._parent.send(ack, host, port)
            request.acknowledged = True