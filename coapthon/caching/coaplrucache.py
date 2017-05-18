from cachetools import LRUCache
from coapthon.caching.coapcache import CoapCache
import six

__author__ = 'Emilio Vallati'


class CoapLRUCache(CoapCache):
    def __init__(self, max_dim):
        """

        :param max_dim:
        """
        self.cache = LRUCache(maxsize=max_dim)

    def update(self, key, element):
        """

        :param key:
        :param element:
        :return:
        """
        six.print_("updating cache")
        six.print_("key: ", key.hashkey)
        six.print_("element: ", element)
        self.cache.update([(key.hashkey, element)])

    def get(self, key):
        """

        :param key:
        :return: CacheElement
        """
        try:
            response = self.cache[key.hashkey]
        except KeyError:
            six.print_("problem here")
            response = None
        return response

    def is_full(self):
        """
        :return:
        """
        if self.cache.currsize == self.cache.maxsize:
            return True
        return False

    def is_empty(self):
        """

        :return:
        """

        if self.cache.currsize == 0:
            return True
        return False

    def debug_print(self):
        """

        :return:
        """
        six.print_("size = ", self.cache.currsize)
        list = self.cache.items()
        for key, element in list:
            six.print_("element.max age ", element.max_age)
            six.print_("element.uri", element.uri)
            six.print_("element.freshness ", element.freshness)

