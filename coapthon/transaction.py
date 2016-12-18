import threading

__author__ = 'Giacomo Tanganelli'


class Transaction(object):
    def __init__(self, request=None, response=None, resource=None, timestamp=None):
        self._response = response
        self._request = request
        self._resource = resource
        self._timestamp = timestamp
        self._completed = False
        self._block_transfer = False
        self.notification = False
        self.separate_timer = None
        self.retransmit_thread = None
        self.retransmit_stop = None
        self._lock = threading.RLock()

        self.cacheHit = False
        self.cached_element = None

    def __enter__(self):
        self._lock.acquire()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._lock.release()

    @property
    def response(self):
        """

        """
        return self._response

    @response.setter
    def response(self, value):
        """

        :type value: Response
        :param value:
        """
        self._response = value

    @property
    def request(self):
        """

        """
        return self._request

    @request.setter
    def request(self, value):
        """

        :type value: Request
        :param value:
        """
        self._request = value

    @property
    def resource(self):
        """

        """
        return self._resource

    @resource.setter
    def resource(self, value):
        """

        :type value: Resource
        :param value:
        """
        self._resource = value

    @property
    def timestamp(self):
        return self._timestamp

    @timestamp.setter
    def timestamp(self, t):
        self._timestamp = t

    @property
    def completed(self):
        return self._completed

    @completed.setter
    def completed(self, b):
        assert isinstance(b, bool)
        self._completed = b

    @property
    def block_transfer(self):
        return self._block_transfer

    @block_transfer.setter
    def block_transfer(self, b):
        assert isinstance(b, bool)
        self._block_transfer = b
