
from coapthon.defines import Codes

from coapthon.caching.cache import *

__author__ = 'Emilio Vallati'


class CacheLayer(object):

    def __init__(self, mode, max_dim=2048):
        """

        :param max_dim:
        """
        self.cache = Cache(mode, max_dim)

    def receive_request(self, transaction):
        """
        checks the cache for a response to the request

        :param transaction:
        :return:
        """

        transaction.cached_element = self.cache.search_response(transaction.request)

        if transaction.cached_element is None:
            transaction.cacheHit = False
        else:
            transaction.response = transaction.cached_element.cached_response
            transaction.response.mid = transaction.request.mid
            transaction.cacheHit = True
            age = transaction.cached_element.creation_time + transaction.cached_element.max_age - time.time()
            if age <= 0:
                print "resource not fresh"
                """
                if the resource is not fresh, its Etag must be added to the request so that the server might validate it instead of sending a new one
                """
                transaction.cached_element.freshness = False
                """
                ensuring that the request goes to the server
                """
                transaction.cacheHit = False
                print "requesting etag ", transaction.response.etag
                transaction.request.etag = transaction.response.etag
            else:
                transaction.response.max_age = age
        return transaction

    def send_response(self, transaction):
        """
        updates the cache with the response if there was a cache miss

        :param transaction:
        :return:
        """
        if transaction.cacheHit is False:
            """
            handling response based on the code
            """
            print "handling response"
            self._handle_response(transaction)
        return transaction

    def _handle_response(self, transaction):
        """
        handles responses based on their type

        :param transaction:
        :return:
        """
        code = transaction.response.code
        utils.check_code(code)
        """
        VALID response:
        change the current cache value by switching the option set with the one provided
        also resets the timestamp
        if the request etag is different from the response, send the cached response
        """
        if code == Codes.VALID.number:
            print "received VALID"
            self.cache.validate(transaction.request, transaction.response)
            if transaction.request.etag != transaction.response.etag:
                element = self.cache.search_response(transaction.request)
                transaction.response = element.cached_response
            return transaction

        """
        CHANGED, CREATED or DELETED response:
        mark the requested resource as not fresh
        """
        if code == Codes.CHANGED.number or code == Codes.CREATED.number or code == Codes.DELETED.number:
            self.cache.mark(transaction.request)
            return transaction

        """
        any other response code can be cached normally
        """
        self.cache.cache_add(transaction.request, transaction.response)
        return transaction

