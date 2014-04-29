from coapthon2 import defines

__author__ = 'giacomo'


class OptionRegistry(object):
    ## The Constant DEFAULT_MAX_AGE. ##
    DEFAULT_MAX_AGE_VALUE = 60

    dict = {
        0: ('Reserved', defines.UNKNOWN),
        1: ('If-Match', defines.OPAQUE),
        3: ('Uri-Host', defines.STRING),
        4: ('ETag', defines.OPAQUE),
        5: ('If-None-Match', defines.INTEGER),
        6: ('Observe', defines.INTEGER),
        7: ('Uri-Port', defines.INTEGER),
        8: ('Location-Path', defines.STRING),
        11: ('Uri-Path', defines.STRING),
        12: ('Content-Type', defines.INTEGER),
        14: ('Max-Age', defines.INTEGER),
        15: ('Uri-Query', defines.STRING),
        17: ('Accept', defines.INTEGER),
        20: ('Location-Query', defines.STRING),
        23: ('Block2', defines.INTEGER),
        27: ('Block1', defines.INTEGER),
        35: ('Proxy-Uri', defines.STRING),
        39: ('Proxy-Scheme', defines.STRING),
        60: ('Size1', defines.INTEGER)
    }