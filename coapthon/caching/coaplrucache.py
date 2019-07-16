import logging

from cachetools import LRUCache
from coapthon.caching.coapcache import CoapCache

__author__ = 'Emilio Vallati'

logger = logging.getLogger(__name__)


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
        logger.debug("updating cache, key: %s, element: %s", \
                key.hashkey, element)
        self.cache.update([(key.hashkey, element)])

    def get(self, key):
        """

        :param key:
        :return: CacheElement
        """
        try:
            response = self.cache[key.hashkey]
        except KeyError:
            logger.debug("problem here", exc_info=1)
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
        return ("size = %s\n%s" % (
            self.cache.currsize,
            '\n'.join([
                (   "element.max age %s\n"\
                    "element.uri %s\n"\
                    "element.freshness %s"  ) % (
                        element.max_age,
                        element.uri,
                        element.freshness )
                for key, element
                in list(self.cache.items())
            ])))
