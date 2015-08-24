from coapthon import defines

__author__ = 'Giacomo Tanganelli'
__version__ = "2.0"


def byte_len(int_type):
    """
    Get the number of bits needed to encode the int passed.

    :param int_type: the int to be converted
    :return: the number of bits needed to encode the int passed.
    """
    length = 0
    while int_type:
        int_type >>= 1
        length += 1
    if length > 0:
        if length % 8 != 0:
            length = int(length / 8) + 1
        else:
            length = int(length / 8)
    return length


def bit_len(int_type):
    """
    Get the number of bits needed to encode the int passed.

    :param int_type: the int to be converted
    :return: the number of bits needed to encode the int passed.
    """
    length = 0
    while int_type:
        int_type >>= 1
        length += 1
    return length

   
class Tree(object):
    def __init__(self):
        self.tree = {}

    def dump(self):
        return self.tree.keys()

    def with_prefix(self, path):
        ret = []
        for key in self.tree.keys():
            if path.startswith(key):
                ret.append(key)

        if len(ret) > 0:
            return ret
        raise KeyError

    def from_prefix(self, path):
        ret = []
        for key in self.tree.keys():
            if key.startswith(path):
                ret.append(key)

        if len(ret) > 0:
            return ret
        raise KeyError

    def __getitem__(self, item):
        return self.tree[item]

    def __setitem__(self, key, value):
        self.tree[key] = value

    def __delitem__(self, key):
        del self.tree[key]
