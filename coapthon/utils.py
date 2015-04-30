import struct
from coapthon import defines

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


class BitManipulationWriter(object):
    def __init__(self):
        self.stream = bytearray()
        self.tmp = 0
        self.pos_byte = 0
        self.pos_bit = 0
        self.pos = 0
        self.len = 0

    def write_bits(self, num, data):
        num_byte = int(num / 8)
        num_bit = num % 8
        if num_byte == 0 and (self.pos_bit + num_bit) <= 8:
            self.tmp <<= self.pos_bit
            self.tmp |= int(data)
            self.pos_bit += num_bit
            self.pos_bit %= 8
        elif num_byte == 0 and (self.pos_bit + num_bit) > 8:
            # more bytes involved
            self.tmp <<= self.pos_bit
            buf = int(data)
            buf >>= (self.pos_bit + num_bit) - 8
            self.tmp |= buf
            self.stream.append(self.tmp)
            self.tmp = 0
            data <<= 8 - ((self.pos_bit + num_bit) - 8)
            self.tmp = data >> (8 - ((self.pos_bit + num_bit) - 8))
            self.pos_bit += num_bit
            if self.pos_bit >= 8:
                self.pos_byte += 1
            self.pos_bit %= 8
        elif num_byte != 0 and self.pos_bit == 0:
            # only complete bytes and no other pending bits

            if isinstance(data, str):
                data = bytearray(data, "utf-8")
                for b in data:
                    self.stream.append(b)
            elif isinstance(data, bytearray):
                for b in data:
                    self.stream.append(b)
            elif isinstance(data, int):
                i = 0
                v, r = divmod(data, 256)
                while True:
                    if v == 0:
                        for s in range(0, num_byte - i - 1):
                            self.stream.append(0x00)
                        self.stream.append(r)
                        break
                    self.stream.append(v)
                    i += 1
                    v, r = divmod(r, 256)

            else:
                raise AttributeError

            self.pos_byte += num_byte
        else:
            tmp_buf = bytearray()
            tmp = data << num_bit
            tmp_buf.append(tmp)

            self.tmp <<= self.pos_bit
            buf = int(data)
            buf >>= (self.pos_bit + num_bit) - 8
            self.tmp |= buf
            self.stream.append(self.tmp)
            self.tmp = 0
            for b in tmp_buf:
                self.stream.append(b)
                self.pos_byte += num_byte

            self.pos_bit += num_bit
            if self.pos_bit >= 8:
                self.pos_byte += 1
            self.pos_bit %= 8
            self.pos = (self.pos_byte * 8) + self.pos_bit


class BitManipulationReader(object):
    def __init__(self, stream):
        assert isinstance(stream, bytearray)
        self.stream = stream
        self.pos_byte = 0
        self.pos_bit = 0
        self.pos = 0
        self.len = len(self.stream) * 8

    def read_bits(self, num, kind="uint", peek=False):
        num_byte = int(num / 8)
        num_bit = num % 8
        tmp = bytearray()
        if num_byte == 0:
            tmp.append(self.stream[self.pos_byte])
        else:
            for b in self.stream[self.pos_byte:self.pos_byte+num_byte]:
                tmp.append(b)
        ret = None
        if num_bit == 0:
            if kind == "str":
                ret = tmp.decode()
            elif kind == "opaque":
                ret = tmp
            else:
                # unpack to int
                if num_byte == 1:
                    ret = struct.unpack("!B", str(tmp))
                    if isinstance(ret, tuple):
                        ret = ret[0]
                elif num_byte == 2:
                    ret = struct.unpack("!H", str(tmp))
                    if isinstance(ret, tuple):
                        ret = ret[0]
        elif num_bit == 1 and self.pos_bit == 0:
            mask = 0x80
            ret = (tmp[-1] & mask) >> 7
        elif num_bit == 1 and self.pos_bit == 1:
            mask = 0x40
            ret = (tmp[-1] & mask) >> 6
        elif num_bit == 1 and self.pos_bit == 2:
            mask = 0x20
            ret = (tmp[-1] & mask) >> 5
        elif num_bit == 1 and self.pos_bit == 3:
            mask = 0x10
            ret = (tmp[-1] & mask) >> 4
        elif num_bit == 1 and self.pos_bit == 4:
            mask = 0x08
            ret = (tmp[-1] & mask) >> 3
        elif num_bit == 1 and self.pos_bit == 5:
            mask = 0x04
            ret = (tmp[-1] & mask) >> 2
        elif num_bit == 1 and self.pos_bit == 6:
            mask = 0x02
            ret = (tmp[-1] & mask) >> 1
        elif num_bit == 1 and self.pos_bit == 7:
            mask = 0x01
            ret = (tmp[-1] & mask)
        elif num_bit == 2 and self.pos_bit == 0:
            mask = 0xC0
            ret = (tmp[-1] & mask) >> 6
        elif num_bit == 2 and self.pos_bit == 1:
            mask = 0x60
            ret = (tmp[-1] & mask) >> 5
        elif num_bit == 2 and self.pos_bit == 2:
            mask = 0x30
            ret = (tmp[-1] & mask) >> 4
        elif num_bit == 2 and self.pos_bit == 3:
            mask = 0x18
            ret = (tmp[-1] & mask) >> 3
        elif num_bit == 2 and self.pos_bit == 4:
            mask = 0x0C
            ret = (tmp[-1] & mask) >> 2
        elif num_bit == 2 and self.pos_bit == 5:
            mask = 0x06
            ret = (tmp[-1] & mask) >> 1
        elif num_bit == 2 and self.pos_bit == 6:
            mask = 0x03
            ret = (tmp[-1] & mask)
        elif num_bit == 2 and self.pos_bit == 7:
            # Cross byte
            mask = 0x01
            mask2 = 0x80
            ret = (tmp[-2] & mask) << 1
            ret2 = (tmp[-1] & mask2) >> 7
            ret |= ret2
        elif num_bit == 3 and self.pos_bit == 0:
            mask = 0xE0
            ret = (tmp[-1] & mask) >> 5
        elif num_bit == 3 and self.pos_bit == 1:
            mask = 0x70
            ret = (tmp[-1] & mask) >> 4
        elif num_bit == 3 and self.pos_bit == 2:
            mask = 0x38
            ret = (tmp[-1] & mask) >> 3
        elif num_bit == 3 and self.pos_bit == 3:
            mask = 0x1C
            ret = (tmp[-1] & mask) >> 2
        elif num_bit == 3 and self.pos_bit == 4:
            mask = 0x0E
            ret = (tmp[-1] & mask) >> 1
        elif num_bit == 3 and self.pos_bit == 5:
            mask = 0x07
            ret = (tmp[-1] & mask)
        elif num_bit == 3 and self.pos_bit == 6:
            # Cross byte
            mask = 0x03
            mask2 = 0x80
            ret = (tmp[-2] & mask) << 1
            ret2 = (tmp[-1] & mask2) >> 7
            ret |= ret2
        elif num_bit == 3 and self.pos_bit == 7:
            # Cross byte
            mask = 0x01
            mask2 = 0xC0
            ret = (tmp[-2] & mask) << 2
            ret2 = (tmp[-1] & mask2) >> 6
            ret |= ret2
        elif num_bit == 4 and self.pos_bit == 0:
            mask = 0xF0
            ret = (tmp[-1] & mask) >> 4
        elif num_bit == 4 and self.pos_bit == 1:
            mask = 0x78
            ret = (tmp[-1] & mask) >> 3
        elif num_bit == 4 and self.pos_bit == 2:
            mask = 0x3C
            ret = (tmp[-1] & mask) >> 2
        elif num_bit == 4 and self.pos_bit == 3:
            mask = 0x1E
            ret = (tmp[-1] & mask) >> 1
        elif num_bit == 4 and self.pos_bit == 4:
            mask = 0x0F
            ret = (tmp[-1] & mask)
        elif num_bit == 4 and self.pos_bit == 5:
            # Cross byte
            mask = 0x07
            mask2 = 0x80
            ret = (tmp[-2] & mask) << 1
            ret2 = (tmp[-1] & mask2) >> 7
            ret |= ret2
        elif num_bit == 4 and self.pos_bit == 6:
            # Cross byte
            mask = 0x03
            mask2 = 0xC0
            ret = (tmp[-2] & mask) << 2
            ret2 = (tmp[-1] & mask2) >> 6
            ret |= ret2
        elif num_bit == 4 and self.pos_bit == 7:
            # Cross byte
            mask = 0x01
            mask2 = 0xE0
            ret = (tmp[-2] & mask) << 3
            ret2 = (tmp[-1] & mask2) >> 5
            ret |= ret2
        elif num_bit == 5 and self.pos_bit == 0:
            mask = 0xF8
            ret = (tmp[-1] & mask) >> 3
        elif num_bit == 5 and self.pos_bit == 1:
            mask = 0x7C
            ret = (tmp[-1] & mask) >> 2
        elif num_bit == 5 and self.pos_bit == 2:
            mask = 0x3E
            ret = (tmp[-1] & mask) >> 1
        elif num_bit == 5 and self.pos_bit == 3:
            mask = 0x3F
            ret = (tmp[-1] & mask)
        elif num_bit == 5 and self.pos_bit == 4:
            # Cross byte
            mask = 0x0F
            mask2 = 0x80
            ret = (tmp[-2] & mask) << 1
            ret2 = (tmp[-1] & mask2) >> 7
            ret |= ret2
        elif num_bit == 5 and self.pos_bit == 5:
            # Cross byte
            mask = 0x07
            mask2 = 0xC0
            ret = (tmp[-2] & mask) << 2
            ret2 = (tmp[-1] & mask2) >> 6
            ret |= ret2
        elif num_bit == 5 and self.pos_bit == 6:
            # Cross byte
            mask = 0x03
            mask2 = 0xE0
            ret = (tmp[-2] & mask) << 3
            ret2 = (tmp[-1] & mask2) >> 5
            ret |= ret2
        elif num_bit == 5 and self.pos_bit == 7:
            # Cross byte
            mask = 0x01
            mask2 = 0xF0
            ret = (tmp[-2] & mask) << 4
            ret2 = (tmp[-1] & mask2) >> 4
            ret |= ret2
        elif num_bit == 6 and self.pos_bit == 0:
            mask = 0xFC
            ret = (tmp[-1] & mask) >> 2
        elif num_bit == 6 and self.pos_bit == 1:
            mask = 0x7E
            ret = (tmp[-1] & mask) >> 1
        elif num_bit == 6 and self.pos_bit == 2:
            mask = 0x3F
            ret = (tmp[-1] & mask)
        elif num_bit == 6 and self.pos_bit == 3:
            # Cross byte
            mask = 0x1F
            mask2 = 0x80
            ret = (tmp[-2] & mask) << 1
            ret2 = (tmp[-1] & mask2) >> 7
            ret |= ret2
        elif num_bit == 6 and self.pos_bit == 4:
            # Cross byte
            mask = 0x0F
            mask2 = 0xC0
            ret = (tmp[-2] & mask) << 2
            ret2 = (tmp[-1] & mask2) >> 6
            ret |= ret2
        elif num_bit == 6 and self.pos_bit == 5:
            # Cross byte
            mask = 0x07
            mask2 = 0xE0
            ret = (tmp[-2] & mask) << 3
            ret2 = (tmp[-1] & mask2) >> 5
            ret |= ret2
        elif num_bit == 6 and self.pos_bit == 6:
            # Cross byte
            mask = 0x03
            mask2 = 0xF0
            ret = (tmp[-2] & mask) << 4
            ret2 = (tmp[-1] & mask2) >> 4
            ret |= ret2
        elif num_bit == 6 and self.pos_bit == 7:
            # Cross byte
            mask = 0x01
            mask2 = 0xF8
            ret = (tmp[-2] & mask) << 5
            ret2 = (tmp[-1] & mask2) >> 3
            ret |= ret2
        elif num_bit == 7 and self.pos_bit == 0:
            mask = 0xFE
            ret = (tmp[-1] & mask) >> 1
        elif num_bit == 7 and self.pos_bit == 1:
            mask = 0x7F
            ret = (tmp[-1] & mask)
        elif num_bit == 7 and self.pos_bit == 2:
            # Cross byte
            mask = 0x3F
            mask2 = 0x80
            ret = (tmp[-2] & mask) << 1
            ret2 = (tmp[-1] & mask2) >> 7
            ret |= ret2
        elif num_bit == 7 and self.pos_bit == 3:
            # Cross byte
            mask = 0x1F
            mask2 = 0xC0
            ret = (tmp[-2] & mask) << 2
            ret2 = (tmp[-1] & mask2) >> 6
            ret |= ret2
        elif num_bit == 7 and self.pos_bit == 4:
            # Cross byte
            mask = 0x0F
            mask2 = 0xE0
            ret = (tmp[-2] & mask) << 3
            ret2 = (tmp[-1] & mask2) >> 5
            ret |= ret2
        elif num_bit == 7 and self.pos_bit == 5:
            # Cross byte
            mask = 0x07
            mask2 = 0xF0
            ret = (tmp[-2] & mask) << 4
            ret2 = (tmp[-1] & mask2) >> 4
            ret |= ret2
        elif num_bit == 7 and self.pos_bit == 6:
            # Cross byte
            mask = 0x03
            mask2 = 0xF8
            ret = (tmp[-2] & mask) << 5
            ret2 = (tmp[-1] & mask2) >> 3
            ret |= ret2
        elif num_bit == 7 and self.pos_bit == 7:
            # Cross byte
            mask = 0x01
            mask2 = 0xFE
            ret = (tmp[-2] & mask) << 3
            ret2 = (tmp[-1] & mask2) >> 5
            ret |= ret2

        if not peek:
            self.pos_byte += num_byte
            self.pos_bit += num_bit
            if self.pos_bit >= 8:
                self.pos_byte += 1
            self.pos_bit %= 8
            self.pos = (self.pos_byte * 8) + self.pos_bit

        return ret

    def peek_bits(self, num):
        return self.read_bits(num, peek=True)


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
        return i.children.get(str(path), None)

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