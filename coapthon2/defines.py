__author__ = 'Giacomo Tanganelli'
__version__ = "2.0"

################### CoAP Parameters ###################
ACK_TIMEOUT = 2

SEPARATE_TIMEOUT = ACK_TIMEOUT / 2

ACK_RANDOM_FACTOR = 1.5

MAX_RETRANSMIT = 4

NSTART = 1

DEFAULT_LEISURE = 5

PROBING_RATE = 1

MAX_TRANSMIT_SPAN = ACK_TIMEOUT * (pow(2, (MAX_RETRANSMIT + 1)) - 1) * ACK_RANDOM_FACTOR

MAX_LATENCY = 120  # 2 minutes

PROCESSING_DELAY = ACK_TIMEOUT

MAX_RTT = (2 * MAX_LATENCY) + PROCESSING_DELAY

EXCHANGE_LIFETIME = MAX_TRANSMIT_SPAN + (2 * MAX_LATENCY) + PROCESSING_DELAY

NON_LIFETIME = MAX_TRANSMIT_SPAN + MAX_LATENCY

DISCOVERY_URL = ".well-known/core"

ALL_COAP_NODES = "224.0.1.187"

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
    0: ('Reserved', UNKNOWN, True, None),
    1: ('If-Match', OPAQUE, True, None),
    3: ('Uri-Host', STRING, False, None),
    4: ('ETag', OPAQUE, True, None),
    5: ('If-None-Match', INTEGER, False, None),
    6: ('Observe', INTEGER, False, None),
    7: ('Uri-Port', INTEGER, False, 5683),
    8: ('Location-Path', STRING, True, None),
    11: ('Uri-Path', STRING, True, None),
    12: ('Content-Type', INTEGER, False, 0),
    14: ('Max-Age', INTEGER, False, 60),
    15: ('Uri-Query', STRING, True, None),
    17: ('Accept', INTEGER, False, 0),
    20: ('Location-Query', STRING, True, None),
    23: ('Block2', INTEGER, False, None),
    27: ('Block1', INTEGER, False, None),
    35: ('Proxy-Uri', STRING, False, None),
    39: ('Proxy-Scheme', STRING, False, None),
    60: ('Size1', INTEGER, False, None)
}

inv_options = {v[0]: k for k, v in options.iteritems()}

################### CoAP Code ###################
codes = {
    0: 'EMPTY',
    1: 'GET',
    2: 'POST',
    3: 'PUT',
    4: 'DELETE',
}

inv_codes = {v: k for k, v in codes.iteritems()}
################### CoAP Type ###################
types = {
    0: 'CON',
    1: 'NON',
    2: 'ACK',
    3: 'RST'
}

inv_types = {v: k for k, v in types.iteritems()}
################### CoAP Response ###################
responses = {
    "CREATED": 65,
    "DELETED": 66,
    "VALID": 67,
    "CHANGED": 68,
    "CONTENT": 69,
    "CONTINUE": 95,
    "BAD_REQUEST": 128,
    "UNAUTHORIZED": 129,
    "BAD_OPTION": 130,
    "FORBIDDEN": 131,
    "NOT_FOUND": 132,
    "METHOD_NOT_ALLOWED": 133,
    "NOT_ACCEPTABLE": 134,
    "REQUEST_ENTITY_INCOMPLETE": 136,
    "PRECONDITION_FAILED": 140,
    "REQUEST_ENTITY_TOO_LARGE": 141,
    "UNSUPPORTED_CONTENT_FORMAT": 143,
    "INTERNAL_SERVER_ERROR": 160,
    "NOT_IMPLEMENTED": 161,
    "BAD_GATEWAY": 162,
    "SERVICE_UNAVAILABLE": 163,
    "GATEWAY_TIMEOUT": 164,
    "PROXY_NOT_SUPPORTED": 165
}

inv_responses = {v: k for k, v in responses.iteritems()}
################### CoAP Content-Type ###################
content_types = {
    0: "text/plain",
    40: "application/link-format",
    41: "application/xml",
    42: "application/octet-stream",
    47: "application/exi",
    50: "application/json"
}

inv_content_types = {v: k for k, v in content_types.iteritems()}


corelinkformat = {
    "ct": "content_type",
    "rt": "resource_type",
    "if": "interface_type",
    "sz": "maximum_size_estimated"
}