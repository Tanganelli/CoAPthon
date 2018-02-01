import time

import logging

from coaplrucache import CoapLRUCache
from coapthon import utils
from coapthon.messages.request import *

__author__ = 'Emilio Vallati'

logger = logging.getLogger(__name__)


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
        logger.debug("adding response to the cache")

        """
        checking for valid code
-       """
        code = response.code
        try:
            utils.check_code(code)
        except utils.InvalidResponseCode:  # pragma no cover
            logger.error("Invalid response code")
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

        logger.debug("MaxAge = {maxage}".format(maxage=response.max_age))
        new_element = CacheElement(new_key, response, request, response.max_age)

        self.cache.update(new_key, new_element)
        logger.debug("Cache Size = {size}".format(size=self.cache.debug_print()))

    def search_related(self, request):
        logger.debug("Cache Search Request")
        if self.cache.is_empty() is True:
            logger.debug("Empty Cache")
            return None

        """
        extracting everything from the cache
        """
        result = []
        items = self.cache.cache.items()

        for key, item in items:
            element = self.cache.get(item.key)
            logger.debug("Element : {elm}".format(elm=str(element)))

            if request.proxy_uri == element.uri:
                result.append(item)

        return result

    def search_response(self, request):
        """
        creates a key from the request and searches the cache with it

        :param request:
        :return CacheElement: returns None if there's a cache miss
        """
        logger.debug("Cache Search Response")

        if self.cache.is_empty() is True:
            logger.debug("Empty Cache")
            return None

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
        :param element:
        :return:
        """
        logger.debug("Element : {elm}".format(elm=str(element)))
        if element is not None:
            logger.debug("Mark as not fresh")
            element.freshness = False
        logger.debug(str(self.cache))

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

    def __str__(self):
        return "Key: {key}, Fresh: {fresh}, URI: {uri}, MaxAge: {maxage}, CreationTime: {ct}, Response: {resp}"\
            .format(key=str(self.key), fresh=self.freshness, uri=self.uri, maxage=self.max_age, ct=self.creation_time,
                    resp=str(self.cached_response))

"""
class for the key used to search elements in the cache (forward-proxy only)
"""


class CacheKey(object):
    def __init__(self, request):
        """

        :param request:
        """
        logger.debug("Creating Key")
        self._payload = request.payload
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
        logger.debug(self)

    def __str__(self):
        msg = ""
        for opt in self._options:
            msg += "{name}: {value}, ".format(name=opt.name, value=opt.value)
        return "Payload: {p}, Method: {m}, Options: [{o}]".format(p=self._payload, m=self._method, o=msg)

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

    def __str__(self):
        msg = ""
        for opt in self._options:
            msg += "{name}: {value}, ".format(name=opt.name, value=opt.value)
        return "Payload: {p}, Method: {m}, Options: [{o}]".format(p=self._payload, m=self._method, o=msg)




