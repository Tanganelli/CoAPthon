from coapthon2.layers.matcher import Matcher
from coapthon2.layers.reliability import Reliability

__author__ = 'Giacomo Tanganelli'


class Layer(object):
    layer_stack = [Reliability(), Matcher()]
    index = 0

    @property
    def next(self):
        layer = self.layer_stack[self.index]
        self.index += 1
        return layer