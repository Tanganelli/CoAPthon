__author__ = 'Emilio Vallati'


class CoapCache:
    def __init__(self, max_dim):
        """

        :param max_dim:
        """
        self.cache = None

    def update(self, key, element):
        """

        :param key:
        :param element:
        :return:
        """
        raise NotImplementedError

    def get(self, key):
        """

        :param key:
        :return: CacheElement
        """
        raise NotImplementedError

    def is_full(self):
        """

        :return:
        """
        raise NotImplementedError

    def is_empty(self):
        """

        :return:
        """
        raise NotImplementedError

    def debug_print(self):
        """

        :return:
        """
        raise NotImplementedError
