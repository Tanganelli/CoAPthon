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
        print "updating cache"
        print "key: ", key.hashkey
        print "element: ", element
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

    def __str__(self):
        msg = []
        for e in self.cache.values():
            msg.append(str(e))
        return "Cache Size: {sz}\n" + "\n".join(msg)

    def debug_print(self):
        """

        :return:
        """
        print "size = ", self.cache.currsize
        list = self.cache.items()
        for key, element in list:
            print "element.max age ", element.max_age
            print "element.uri", element.uri
            print "element.freshness ", element.freshness

