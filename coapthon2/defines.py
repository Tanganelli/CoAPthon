__author__ = 'giacomo'

################### Message Format ###################

## number of bits used for the encoding of the CoAP version field.
VERSION_BITS = 2

## number of bits used for the encoding of the message type field.
TYPE_BITS = 2

## number of bits used for the encoding of the token length field.
TOKEN_LENGTH_BITS = 4

## number of bits used for the encoding of the request method/response code field.
CODE_BITS = 8

## number of bits used for the encoding of the message ID.
MESSAGE_ID_BITS = 16

## number of bits used for the encoding of the option delta field.
OPTION_DELTA_BITS = 4

## number of bits used for the encoding of the option delta field.
OPTION_LENGTH_BITS = 4

## One byte which indicates indicates the end of options and the start of the payload.
PAYLOAD_MARKER = 0xFF

## CoAP version supported by this Californium version.
VERSION = 1

## The code value of an empty message.
EMPTY_CODE = 0

## The lowest value of a request code.
REQUEST_CODE_LOWER_BOUND = 1

## The highest value of a request code.
REQUEST_CODE_UPPER_BOUNT = 31

## The lowest value of a response code.
RESPONSE_CODE_LOWER_BOUND = 64

## The highest value of a response code.
RESPONSE_CODE_UPPER_BOUND = 191

################### Option ###################

## The integer.
INTEGER = 0
## The string.
STRING = 1
## The opaque.
OPAQUE = 2
## The unknown.
UNKNOWN = 3

#(NAME, VALUE_TYPE, REPEATABLE)
options = {
    0: ('Reserved', UNKNOWN, True),
    1: ('If-Match', OPAQUE, True),
    3: ('Uri-Host', STRING, False),
    4: ('ETag', OPAQUE, True),
    5: ('If-None-Match', INTEGER, False),
    6: ('Observe', INTEGER, False),
    7: ('Uri-Port', INTEGER, False),
    8: ('Location-Path', STRING, True),
    11: ('Uri-Path', STRING, True),
    12: ('Content-Type', INTEGER, False),
    14: ('Max-Age', INTEGER, False),
    15: ('Uri-Query', STRING, True),
    17: ('Accept', INTEGER, False),
    20: ('Location-Query', STRING, True),
    23: ('Block2', INTEGER, False),
    27: ('Block1', INTEGER, False),
    35: ('Proxy-Uri', STRING, False),
    39: ('Proxy-Scheme', STRING, False),
    60: ('Size1', INTEGER, False)
}

################### CoAP Code ###################
codes = {
    1: 'GET',
    2: 'POST',
    3: 'PUT',
    4: 'DELETE',
}
