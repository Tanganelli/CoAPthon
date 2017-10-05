import logging

from coapthon.defines import Codes

from coapthon.caching.cache import *

__author__ = 'Emilio Vallati'

logger = logging.getLogger(__name__)


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
            if transaction.cached_element.freshness is True:
                if age <= 0:
                    logger.debug("resource not fresh")
                    """
                    if the resource is not fresh, its Etag must be added to the request so that the server might validate it instead of sending a new one
                    """
                    transaction.cached_element.freshness = False
                    """
                    ensuring that the request goes to the server
                    """
                    transaction.cacheHit = False
                    logger.debug("requesting etag %s", transaction.response.etag)
                    transaction.request.etag = transaction.response.etag
                else:
                    transaction.response.max_age = age
            else:
                transaction.cacheHit = False
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
            logger.debug("handling response")
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
            logger.debug("received VALID")
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
            target = self.cache.search_related(transaction.request)
            if target is not None:
                for element in target:
                    self.cache.mark(element)
            return transaction

        """
        any other response code can be cached normally
        """
        self.cache.cache_add(transaction.request, transaction.response)
        return transaction

