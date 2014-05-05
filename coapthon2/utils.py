__author__ = 'Giacomo Tanganelli'
__version__ = "2.0"


def bit_len(int_type):
    length = 0
    while int_type:
        int_type >>= 1
        length += 1
    length = int(length / 8) + 1
    return length


class Tree(object):
    def __init__(self, value, parent=None, children=None):
        self.value = value
        self.parent = parent
        if children is None:
            self.children = {}
        else:
            self.children = children

    def find_complete(self, path):
        paths = path.split("/")
        start = self
        res = None
        for p in paths:
            res = self.find(p, start)
            if res is None:
                return None
            else:
                start = res
        return res

    def find(self, path, tree=None):
        if tree is None:
            i = self
        else:
            i = tree
        assert isinstance(i, Tree)
        return i.children.get(path, None)

    def add_child(self, resource):
        if resource.path not in self.children:
            new = Tree(resource, self)
            self.children[resource.path] = new
        else:
            new = self.children.get(resource.path)
        return new

    def dump(self, msg="", tab=""):
        msg += tab + "[" + self.value.path + " Name: " + self.value.name + "]\n\t"
        for i in self.children:
            v = self.children.get(i, None)
            if v is not None:
                assert isinstance(v, Tree)
                tab += "\t"
                return v.dump(msg, tab)
        return msg