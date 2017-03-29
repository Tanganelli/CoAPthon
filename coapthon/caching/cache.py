import time

from coaplrucache import CoapLRUCache
from coapthon import utils
from coapthon.messages.request import *
from coapthon.messages.message import Message


__author__ = 'Emilio Vallati'


class Cache(object):

    def __init__(self, mode, max_dim):
        """

        :param max_dim: max number of elements in the cache
        :param mode: used to differentiate between a cache used in a forward-proxy or in a reverse-proxy
        """

        self.max_dimension = max_dim
        self.mode = mode
        self.cache = CoapLRUCache(max_dim)

    def cache_add(self, request, response):
        """
        checks for full cache and valid code before updating the cache

        :param request:
        :param response:
        :return:
        """
        print "adding response to the cache"

        """
        checking for valid code
-       """
        code = response.code
        try:
            utils.check_code(code)
        except utils.InvalidResponseCode:
            print "Invalid response code"
            return

        """
        return if max_age is 0
        """
        if response.max_age == 0:
            return

        """
        Initialising new cache element based on the mode and updating the cache
        """

        if self.mode == defines.FORWARD_PROXY:
            new_key = CacheKey(request)
        else:
            new_key = ReverseCacheKey(request)

        print "max age = ", response.max_age
        new_element = CacheElement(new_key, response, request, response.max_age)

        self.cache.update(new_key, new_element)
        print "cache size = ", self.cache.debug_print()



    def search_related(self, request):
        print "searching similar payload"
        if self.cache.is_empty() is True:
            print "empty cache"
            return None

        print "cache not empty"

        """
        extracting everything from the cache
        """
        result = []
        items = self.cache.cache.items()
        for key, item in items:
            print "key = ", key
            print "item = ", item

        for key, item in items:
            element = self.cache.get(item.key)
            print "element.uri: ", element.uri
            print "uri path: ", request.proxy_uri
            if request.proxy_uri == element.uri:
                result.append(item)

        return result


    def search_response(self, request):
        """
        creates a key from the request and searches the cache with it

        :param request:
        :return CacheElement: returns None if there's a cache miss
        """
        print "searching response"

        if self.cache.is_empty() is True:
            print "empty cache"
            return None

        print "cache not empty"

        """
        create a new cache key from the request
        """

        if self.mode == defines.FORWARD_PROXY:
            search_key = CacheKey(request)
        else:
            search_key = ReverseCacheKey(request)

        response = self.cache.get(search_key)

        return response


    def validate(self, request, response):
        """
        refreshes a resource when a validation response is received

        :param request:
        :param response:
        :return:
        """
        element = self.search_response(request)
        if element is not None:
            element.cached_response.options = response.options
            element.freshness = True
            element.max_age = response.max_age
            element.creation_time = time.time()
            element.uri = request.proxy_uri

    def mark(self, element):
        """
        marks the requested resource in the cache as not fresh
        :param request:
        :return:
        """
        print "element.response = ", element.cached_response
        print "element.uri = ", element.uri
        print "element.freshness = ", element.freshness
        if element is not None:
            print "unfreshening"
            element.freshness = False
        self.cache.debug_print()

"""
class for the element contained in the cache
"""


class CacheElement(object):
    def __init__(self, cache_key, response, request,  max_age=60):
        """

        :param cache_key: the key used to search for the element in the cache
        :param response: the server response to store
        :param max_age: maximum number of seconds that the resource is considered fresh
        """
        self.freshness = True
        self.key = cache_key
        self.cached_response = response
        self.max_age = max_age
        self.creation_time = time.time()
        self.uri = request.proxy_uri

    def debug_print(self):
        print "freshness = ", self.freshness
        print "key"
        self.key.debug_print()
        print "response = ", self.cached_response
        print "max age = ", self.max_age
        print "creation time = ", self.creation_time

"""
class for the key used to search elements in the cache (forward-proxy only)
"""


class CacheKey(object):
    def __init__(self, request):
        """

        :param request:
        """
        print "creating key"
        if (request.payload is not None):
            self._payload = request.payload
        else:
            self._payload = None
        self._method = request.code

        """
        making a list of the options that do not have a nocachekey option number and are not uri-path, uri-host, uri-port, uri-query
        """

        self._options = []
        for option in request.options:
            if (utils.check_nocachekey(option) is False) and (utils.is_uri_option(option.number) is False):
                self._options.append(option)

        """
        creating a usable key for the cache structure
        """

        option_str = ', '.join(map(str, self._options))
        self._list = [self._payload, self._method, option_str]

        self.hashkey = ', '.join(map(str, self._list))
        self.debug_print()

    def debug_print(self):
        print "payload = ", self._payload
        print "method = ", self._method
        print "options = "
        for option in self._options:
            print option


"""
class for the key used to search elements in the cache (reverse-proxy only)
"""


class ReverseCacheKey(object):
    def __init__(self, request):
        """

        :param request:
        """
        self._payload = request.payload
        self._method = request.code

        """
        making a list of the options that do not have a nocachekey option number
        """

        self._options = []
        for option in request.options:
            if utils.check_nocachekey(option) is False:
                self._options.append(option)

        """
        creating a usable key for the cache structure
        """

        option_str = ', '.join(map(str, self._options))
        self.hashkey = (self._payload, self._method, option_str)

    def debug_print(self):
        print "payload = ", self._payload
        print "method = ", self._method
        print "options = "
        for option in self._options:
            print option


