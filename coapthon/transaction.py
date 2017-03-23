import threading

__author__ = 'Giacomo Tanganelli'


class Transaction(object):
    """
    Transaction object to bind together a request, a response and a resource.
    """
    def __init__(self, request=None, response=None, resource=None, timestamp=None):
        """
        Initialize a Transaction object.

        :param request: the request
        :param response: the response
        :param resource: the resource interested by the transaction
        :param timestamp: the timestamp of the transaction
        """
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
        Return the response.

        :return: the response
        :rtype: Response
        """
        return self._response

    @response.setter
    def response(self, value):
        """
        Set the response.

        :type value: Response
        :param value: the response to be set in the transaction
        """
        self._response = value

    @property
    def request(self):
        """
        Return the request.

        :return: the request
        :rtype: Request
        """
        return self._request

    @request.setter
    def request(self, value):
        """
        Set the request.

        :type value: Request
        :param value: the request to be set in the transaction
        """
        self._request = value

    @property
    def resource(self):
        """
        Return the resource.

        :return: the resource
        :rtype: Resource
        """
        return self._resource

    @resource.setter
    def resource(self, value):
        """
        Set the resource.

        :type value: Resource
        :param value: the resource to be set in the transaction
        """
        self._resource = value

    @property
    def timestamp(self):
        """
        Return the timestamp.

        :return: the timestamp
        """
        return self._timestamp

    @timestamp.setter
    def timestamp(self, t):
        """
        Set the timestamp.

        :param t: the timestamp of the transaction
        """
        self._timestamp = t

    @property
    def completed(self):
        """
        Return the completed attribute.

        :return: True, if transaction is completed
        """
        return self._completed

    @completed.setter
    def completed(self, b):
        """
        Set the completed attribute.

        :param b: the completed value
        :type b: bool
        """
        assert isinstance(b, bool)
        self._completed = b

    @property
    def block_transfer(self):
        """
        Return the block_transfer attribute.

        :return: True, if transaction is blockwise
        """
        return self._block_transfer

    @block_transfer.setter
    def block_transfer(self, b):
        """
        Set the block_transfer attribute.

        :param b: the block_transfer value
        :type b: bool
        """
        assert isinstance(b, bool)
        self._block_transfer = b
