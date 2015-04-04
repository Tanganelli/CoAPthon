from coapthon2 import defines

__author__ = 'Giacomo Tanganelli'
__version__ = "2.0"


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
    length = int(length / 8) + 1
    return length


class Tree(object):
    def __init__(self, value, parent=None, children=None):
        """
        Create a node.

        :param value: the node value
        :param parent: the parent of the node
        :param children: the children of the node
        """
        self.value = value
        self.parent = parent
        if children is None:
            self.children = {}
        else:
            self.children = children

    def find_path(self, msg=""):
        """
        Find the absolute path of a node

        :return : path
        """
        msg = self.value.path + "/" + msg
        if self.parent is not None:
            return self.parent.find_path(msg)
        return msg[1:]

    def find_complete_last(self, paths):
        """
        Find a node and its last path

        :type paths: list of string
        :param paths: the path as list of string item
        :return: the node and its last path
        """
        start = self
        res = None
        for p in paths:
            res = self.find(p, start)
            if res is None:
                return start, p
            else:
                start = res
        return res, None

    def find_complete(self, path):
        """
        Find a node based on a path.

        :type path: sting
        :param path: the path to search for
        :return: the node or None
        """
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
        """
        Search path in the children

        :param path: the path to search for
        :param tree: the starting node, if None then tree=self
        :return: the children or None
        """
        if tree is None:
            i = self
        else:
            i = tree
        assert isinstance(i, Tree)
        return i.children.get(path, None)

    def add_child(self, resource):
        """
        Add a child to the children of the node.

        :param resource: the resource to add
        :return:the new node
        """
        if resource.path not in self.children:
            new = Tree(resource, self)
            self.children[resource.path] = new
        else:
            new = self.children.get(resource.path)
            new.value = resource
        return new

    def dump(self, msg="", tab=""):
        """
        Recursive function, return a formatted string representation of the tree.

        :param msg: the message to be printed
        :param tab: the tab
        :return: the string representation
        """
        msg += tab + "[" + self.value.path + " Name: " + self.value.name + "]\n"
        for i in self.children:
            v = self.children.get(i, None)
            if v is not None:
                assert isinstance(v, Tree)
                tab = "\t"
                msg += v.dump("", tab)
        return msg

    def corelinkformat(self, msg="", parent=""):
        """
        Recursive function, return a formatted string representation of the corelinkformat in the tree.

        :param msg: the message to be printed
        :param parent: the parent node
        :return: the string
        """
        if self.value.name != "root":
            parent += self.value.path + "/"
            msg += "<" + parent[:-1] + ">;"
            for k in self.value.attributes:
                method = getattr(self.value, defines.corelinkformat[k], None)
                if method is not None:
                    v = method
                    msg = msg[:-1] + ";" + str(v) + ","
                else:
                    v = self.value.attributes[k]
                    msg = msg[:-1] + ";" + k + "=" + v + ","
        else:
            parent += self.value.path
        for i in self.children:
            v = self.children.get(i, None)
            if v is not None:
                assert isinstance(v, Tree)
                msg += v.corelinkformat("", parent)
        return msg

    def del_child(self, node):
        """
        Recursive function. Delete all the children of a node

        :param node: the node
        :return: nothing
        """
        assert isinstance(node, Tree)
        for k in node.children:
            v = node.children.get(k, None)
            if v is not None:
                return self.del_child(v)
        try:
            del self.children[node.value.path]
        except KeyError:
            pass