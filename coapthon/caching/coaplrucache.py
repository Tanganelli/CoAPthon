from cachetools import LRUCache
from coapthon.caching.coapcache import CoapCache

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
        self.cache.update([(key.hashkey, element)])

    def get(self, key):
        """

        :param key:
        :return: CacheElement
        """
        try:
            response = self.cache[key.hashkey]
        except KeyError:
            print "problem here"
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
        print "size = ", self.cache.currsize

