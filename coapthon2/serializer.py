import sys
from bitstring import BitStream, ReadError, pack, BitArray
from twisted.python import log
from coapthon2 import defines
from coapthon2.messages.message import Message
from coapthon2.messages.option import Option
from coapthon2.messages.request import Request
from coapthon2.messages.response import Response

__author__ = 'Giacomo Tanganelli'
__version__ = "2.0"


class Serializer(object):
    """
    Class for serialize and de-serialize messages.
    """
    def __init__(self):
        """
        Initialize a Serializer.

        """
        self._reader = None
        self._writer = None

    def deserialize(self, raw, host, port):
        """
        De-serialize a stream of byte to a message.

        :param raw: received bytes
        :param host: source host
        :param port: source port
        :return: the message
        """
        self._reader = BitStream(bytes=raw, length=(len(raw) * 8))
        version = self._reader.read(defines.VERSION_BITS).uint
        message_type = self._reader.read(defines.TYPE_BITS).uint
        token_length = self._reader.read(defines.TOKEN_LENGTH_BITS).uint
        code = self._reader.read(defines.CODE_BITS).uint
        mid = self._reader.read(defines.MESSAGE_ID_BITS).uint
        if self.is_response(code):
            message = Response()
            message.code = code
        elif self.is_request(code):
            message = Request()
            message.code = code
        else:
            message = Message()
        message.source = (host, port)
        message.destination = None
        message.version = version
        message.type = message_type
        message.mid = mid

        if token_length > 0:
            message.token = self._reader.read(token_length * 8).bytes
        else:
            message.token = None

        current_option = 0
        try:
            while self._reader.pos < self._reader.len:
                next_byte = self._reader.peek(8).uint
                if next_byte != int(defines.PAYLOAD_MARKER):
                    # the first 4 bits of the byte represent the option delta
                    delta = self._reader.read(4).uint
                    # the second 4 bits represent the option length
                    length = self._reader.read(4).uint
                    current_option += self.read_option_value_from_nibble(delta)
                    option_length = self.read_option_value_from_nibble(length)

                    # read option
                    try:
                        option_name, option_type, option_repeatable, default = defines.options[current_option]
                    except KeyError:
                        log.err("unrecognized option")
                        return message, "BAD_OPTION"
                    if option_length == 0:
                        value = None
                    elif option_type == defines.INTEGER:
                        value = self._reader.read(option_length * 8).uint
                    else:
                        value = self._reader.read(option_length * 8).bytes

                    option = Option()
                    option.number = current_option
                    option.value = self.convert_to_raw(current_option, value, option_length)

                    message.add_option(option)
                else:
                    self._reader.pos += 8  # skip payload marker
                    if self._reader.len <= self._reader.pos:
                        log.err("Payload Marker with no payload")
                        return message, "BAD_REQUEST"
                    to_end = self._reader.len - self._reader.pos
                    message.payload = self._reader.read(to_end).bytes
            return message
        except ReadError, e:
            log.err("Error parsing message: " + str(e))
        return None

    @staticmethod
    def is_request(code):
        """
        Checks if is request.

        :return: True, if is request
        """
        return defines.REQUEST_CODE_LOWER_BOUND <= code <= defines.REQUEST_CODE_UPPER_BOUNT

    @staticmethod
    def is_response(code):
        """
        Checks if is response.

        :return: True, if is response
        """
        return defines.RESPONSE_CODE_LOWER_BOUND <= code <= defines.RESPONSE_CODE_UPPER_BOUND

    def read_option_value_from_nibble(self, nibble):
        """
        Calculates the value used in the extended option fields.

        :param nibble: the 4-bit option header value.
        :return: the value calculated from the nibble and the extended option value.
        """
        if nibble <= 12:
            return nibble
        elif nibble == 13:
            #self._reader.pos += 4
            tmp = self._reader.read(8).uint + 13
            #self._reader.pos -= 12
            return tmp
        elif nibble == 14:
            return self._reader.read(16).uint + 269
        else:
            raise ValueError("Unsupported option nibble " + nibble)

    def serialize(self, message):
        """
        Serialize message to a stream of byte.

        :param message: the message
        :return: the stream of bytes
        """
        fmt = 'uint:' + str(defines.VERSION_BITS) + '=version,' \
            'uint:' + str(defines.TYPE_BITS) + '=type,' \
            'uint:' + str(defines.TOKEN_LENGTH_BITS) + '=tokenlen,' \
            'uint:' + str(defines.CODE_BITS) + '=code,' \
            'uint:' + str(defines.MESSAGE_ID_BITS) + '=mid'
        d = {'version': defines.VERSION,
             'type': message.type,
             'code': message.code,
             'mid': message.mid}
        if message.token is None or message.token == "":
            d['tokenlen'] = 0
        else:
            d['tokenlen'] = len(message.token)

        self._writer = pack(fmt, **d)

        if message.token is not None and len(message.token) > 0:
            fmt = 'bytes:' + str(len(message.token)) + '=token'
            d = {'token': message.token}
            self._writer.append(pack(fmt, **d))

        options = self.as_sorted_list(message.options)  # already sorted
        lastoptionnumber = 0
        for option in options:

            # write 4-bit option delta
            optiondelta = option.number - lastoptionnumber
            optiondeltanibble = self.get_option_nibble(optiondelta)
            fmt = 'uint:' + str(defines.OPTION_DELTA_BITS) + '=delta'
            d = {'delta': optiondeltanibble}
            self._writer.append(pack(fmt, **d))
            # self._writer.write(optiondeltanibble, defines.OPTION_DELTA_BITS)

            # write 4-bit option length
            optionlength = option.length
            optionlengthnibble = self.get_option_nibble(optionlength)
            fmt = 'uint:' + str(defines.OPTION_LENGTH_BITS) + '=len'
            d = {'len': optionlengthnibble}
            self._writer.append(pack(fmt, **d))
            # self._writer.write(optionlengthnibble, defines.OPTION_LENGTH_BITS)

            # write extended option delta field (0 - 2 bytes)
            if optiondeltanibble == 13:
                fmt = 'uint:8=delta'
                d = {'delta': optiondelta - 13}
                self._writer.append(pack(fmt, **d))
                # self._writer.write(optiondelta - 13, 8)
            elif optiondeltanibble == 14:
                fmt = 'uint:16=delta'
                d = {'delta': optiondelta - 269}
                self._writer.append(pack(fmt, **d))
                # self._writer.write(optiondelta - 269, 16)

            # write extended option length field (0 - 2 bytes)
            if optionlengthnibble == 13:
                fmt = 'uint:8=len'
                d = {'len': optionlength - 13}
                self._writer.append(pack(fmt, **d))
                # self._writer.write(optionlength - 13, 8)
            elif optionlengthnibble == 14:
                fmt = 'uint:16=len'
                d = {'len': optionlength - 269}
                self._writer.append(pack(fmt, **d))
                # self._writer.write(optionlength - 269, 16)

            # write option value
            fmt = 'bytes:'+str(optionlength)+'=option'
            d = {'option': option.raw_value.tobytes()}
            self._writer.append(pack(fmt, **d))
            # self._writer.writeBytes(option.getValue())

            # update last option number
            lastoptionnumber = option.number

        payload = message.payload
        if isinstance(payload, dict):
            payload = payload.get("Payload")
        if payload is not None and len(payload) > 0:
            # if payload is present and of non-zero length, it is prefixed by
            # an one-byte Payload Marker (0xFF) which indicates the end of
            # options and the start of the payload
            fmt = 'uint:8=marker, bytes:' + str(len(payload)) + '=payload'
            d = {'marker': str(defines.PAYLOAD_MARKER), 'payload': payload}
            self._writer.append(pack(fmt, **d))

        return self._writer.tobytes()

    @staticmethod
    def get_option_nibble(optionvalue):
        """
        Returns the 4-bit option header value.

        :param optionvalue: the option value (delta or length) to be encoded.
        :return: the 4-bit option header value.
         """
        if optionvalue <= 12:
            return optionvalue
        elif optionvalue <= 255 + 13:
            return 13
        elif optionvalue <= 65535 + 269:
            return 14
        else:
            raise ValueError("Unsupported option delta " + optionvalue)

    def as_sorted_list(self, options):
        """
        Returns all options in a list sorted according to their option numbers.

        :return: the sorted list
        """
        '''
        if self._if_match_list:
            for value in self._if_match_list:
                options.append(Option(OptionNumberRegistry.IF_MATCH, value))
        if self.uri_host is not None:
            options.append(Option(OptionNumberRegistry.URI_HOST, self.uri_host))
        if self._etag_list:
            for value in self._etag_list:
                options.append(Option(OptionNumberRegistry.ETAG, value))
        if self.if_none_match is not False:
            options.append(Option(OptionNumberRegistry.IF_NONE_MATCH))
        if self.uri_port is not None:
            options.append(Option(OptionNumberRegistry.URI_PORT, self.uri_port))
        if self._location_path_list:
            for s in self._location_path_list:
                options.append(Option(OptionNumberRegistry.LOCATION_PATH, s))
        if self._uri_path_list:
            for s in self._uri_path_list:
                options.append(Option(OptionNumberRegistry.URI_PATH, s))
        if self.content_format is not None:
            options.append(Option(OptionNumberRegistry.CONTENT_TYPE, val=self.content_format))
        if self.max_age is not None and self.max_age != Default.DEFAULT_MAX_AGE:
            options.append(Option(OptionNumberRegistry.MAX_AGE, self.max_age))
        if self._uri_query_list:
            for s in self._uri_query_list:
                options.append(Option(OptionNumberRegistry.URI_QUERY, s))
        if self.accept is not None:
            options.append(Option(OptionNumberRegistry.ACCEPT, self.accept))
        if self._location_query_list:
            for s in self._location_query_list:
                options.append(Option(OptionNumberRegistry.LOCATION_QUERY, s))
        if self.proxy_uri is not None:
            options.append(Option(OptionNumberRegistry.PROXY_URI, self.proxy_uri))
        if self.proxy_scheme is not None:
            options.append(Option(OptionNumberRegistry.PROXY_SCHEME, self.proxy_scheme))
        if self.size1 is not None:
            options.append(Option(OptionNumberRegistry.SIZE1, self.size1))

        if self.block_1 is not None:
            options.append(Option(OptionNumberRegistry.BLOCK1, self.block_1.value))
        if self.block_2 is not None:
            options.append(Option(OptionNumberRegistry.BLOCK2, self.block_2.value))

        if self.observe is not None:
            options.append(Option(OptionNumberRegistry.OBSERVE, self.observe))

        if self._others:
            for s in self._others:
                options.append(s)'''

        ## TODO check sorting
        if len(options) > 0:
            options.sort(None, key=lambda o: o.number)
        return options

    @staticmethod
    def convert_to_raw(number, value, length):
        """
        Get the value of an option as a BitArray.

        :param number: the option number
        :param value: the option value
        :param length: the option length
        :return: the value of an option as a BitArray
        """
        if length == 0:
            return BitArray()
        name, value_type, repeatable, default = defines.options[number]
        if value_type == defines.INTEGER:
            return BitArray(uint=value, length=length * 8)
        else:
            return BitArray(bytes=value, length=length * 8)