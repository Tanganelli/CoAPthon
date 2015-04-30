import ctypes
import struct
from twisted.python import log
from coapthon import defines
from coapthon.messages.message import Message
from coapthon.messages.option import Option
from coapthon.messages.request import Request
from coapthon.messages.response import Response

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
        # stream = bytearray(raw)
        # self._reader = BitManipulationReader(stream)
        # version = self._reader.read_bits(defines.VERSION_BITS, "uint")
        # message_type = self._reader.read_bits(defines.TYPE_BITS, "uint")
        # token_length = self._reader.read_bits(defines.TOKEN_LENGTH_BITS, "uint")
        # code = self._reader.read_bits(defines.CODE_BITS, "uint")
        # mid = self._reader.read_bits(defines.MESSAGE_ID_BITS, "uint")
        # # self._reader = BitStream(bytes=raw, length=(len(raw) * 8))
        # # version = self._reader.read(defines.VERSION_BITS).uint
        # # message_type = self._reader.read(defines.TYPE_BITS).uint
        # # token_length = self._reader.read(defines.TOKEN_LENGTH_BITS).uint
        # # code = self._reader.read(defines.CODE_BITS).uint
        # # mid = self._reader.read(defines.MESSAGE_ID_BITS).uint
        # if self.is_response(code):
        #     message = Response()
        #     message.code = code
        # elif self.is_request(code):
        #     message = Request()
        #     message.code = code
        # else:
        #     message = Message()
        # message.source = (host, port)
        # message.destination = None
        # message.version = version
        # message.type = message_type
        # message._mid = mid
        #
        # if token_length > 0:
        #     # message.token = self._reader.read(token_length * 8).bytes
        #     message.token = self._reader.read_bits(token_length * 8, "str")
        # else:
        #     message.token = None
        #
        # current_option = 0
        # while self._reader.pos < self._reader.len:
        #     # next_byte = self._reader.peek(8).uint
        #     next_byte = self._reader.peek_bits(8)
        #     if next_byte != int(defines.PAYLOAD_MARKER):
        #         # the first 4 bits of the byte represent the option delta
        #         # delta = self._reader.read(4).uint
        #         delta = self._reader.read_bits(4)
        #         # the second 4 bits represent the option length
        #         # length = self._reader.read(4).uint
        #         length = self._reader.read_bits(4)
        #         current_option += self.read_option_value_from_nibble(delta)
        #         option_length = self.read_option_value_from_nibble(length)
        #
        #         # read option
        #         try:
        #             option_name, option_type, option_repeatable, default = defines.options[current_option]
        #         except KeyError:
        #             log.err("unrecognized option")
        #             return message, "BAD_OPTION"
        #         if option_length == 0:
        #             value = None
        #         elif option_type == defines.INTEGER:
        #             # value = self._reader.read(option_length * 8).uint
        #             value = self._reader.read_bits(option_length * 8, "uint")
        #         else:
        #             # value = self._reader.read(option_length * 8).bytes
        #             value = self._reader.read_bits(option_length * 8, kind='str')
        #
        #         option = Option()
        #         option.number = current_option
        #         option.value = self.convert_to_raw(current_option, value, option_length)
        #
        #         message.add_option(option)
        #     else:
        #         # self._reader.pos += 8  # skip payload marker
        #         self._reader.pos_byte += 1  # skip payload marker
        #         if self._reader.len <= self._reader.pos:
        #             log.err("Payload Marker with no payload")
        #             return message, "BAD_REQUEST"
        #         to_end = self._reader.len - self._reader.pos
        #         # message.payload = self._reader.read(to_end).bytes
        #         message.payload = self._reader.read_bits(to_end, "opaque")
        # return message
        # message1 = message

        fmt = "!BBH"
        pos = 4
        length = len(raw)
        while pos < length:
            fmt += "c"
            pos += 1
        s = struct.Struct(fmt)
        self._reader = raw
        values = s.unpack_from(self._reader)
        first = values[0]
        code = values[1]
        mid = values[2]
        version = (first & 0xC0) >> 6
        message_type = (first & 0x30) >> 4
        token_length = (first & 0x0F)
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
        message._mid = mid
        pos = 3
        if token_length > 0:
                message.token = "".join(values[pos: pos + token_length])
        else:
            message.token = None

        pos += token_length
        current_option = 0
        length_packet = len(values)
        while pos < length_packet:
            next_byte = struct.unpack("B", values[pos])[0]
            pos += 1
            if next_byte != int(defines.PAYLOAD_MARKER):
                # the first 4 bits of the byte represent the option delta
                # delta = self._reader.read(4).uint
                delta = (next_byte & 0xF0) >> 4
                # the second 4 bits represent the option length
                # length = self._reader.read(4).uint
                length = (next_byte & 0x0F)
                num, pos = self.read_option_value_from_nibble2(delta, pos, values)
                option_length, pos = self.read_option_value_from_nibble2(length, pos, values)
                current_option += num
                # read option
                try:
                    option_name, option_type, option_repeatable, default = defines.options[current_option]
                except KeyError:
                    log.err("unrecognized option")
                    return message, "BAD_OPTION"
                if option_length == 0:
                    value = None
                elif option_type == defines.INTEGER:

                    tmp = values[pos: pos + option_length]
                    value = 0
                    for b in tmp:
                        value = (value << 8) | b
                else:
                    tmp = values[pos: pos + option_length]
                    value = ""
                    for b in tmp:
                        value += str(b)

                pos += option_length
                option = Option()
                option.number = current_option
                option.value = self.convert_to_raw(current_option, value, option_length)

                message.add_option(option)
            else:

                if length_packet <= pos:
                    log.err("Payload Marker with no payload")
                    return message, "BAD_REQUEST"
                message.payload = ""
                payload = values[pos:]
                for b in payload:
                    message.payload += str(b)
                    pos += 1
        return message


    @staticmethod
    def is_request(code):
        """
        Checks if is request.

        :return: True, if is request
        """
        return defines.REQUEST_CODE_LOWER_BOUND <= code <= defines.REQUEST_CODE_UPPER_BOUND

    @staticmethod
    def is_response(code):
        """
        Checks if is response.

        :return: True, if is response
        """
        return defines.RESPONSE_CODE_LOWER_BOUND <= code <= defines.RESPONSE_CODE_UPPER_BOUND

    def read_option_value_from_nibble2(self, nibble, pos, values):
        """
        Calculates the value used in the extended option fields.

        :param nibble: the 4-bit option header value.
        :return: the value calculated from the nibble and the extended option value.
        """
        if nibble <= 12:
            return nibble, pos
        elif nibble == 13:
            tmp = struct.unpack("B", values[pos])[0] + 13
            pos += 1
            return tmp, pos
        elif nibble == 14:
            tmp = struct.unpack("B", values[pos])[0] + 269
            pos += 2
            return tmp, pos
        else:
            raise ValueError("Unsupported option nibble " + nibble)

    def read_option_value_from_nibble(self, nibble):
        if nibble <= 12:
            return nibble
        elif nibble == 13:
            return self._reader.read_bits(8, "uint") + 13

        elif nibble == 14:
            return self._reader.read_bits(8, "uint") + 269

        else:
            raise ValueError("Unsupported option nibble " + nibble)

    def serialize(self, message):
        """
        Serialize message to a stream of byte.

        :param message: the message
        :return: the stream of bytes
        """
        # fmt = 'uint:' + str(defines.VERSION_BITS) + '=version,' \
        # 'uint:' + str(defines.TYPE_BITS) + '=type,' \
        #     'uint:' + str(defines.TOKEN_LENGTH_BITS) + '=tokenlen,' \
        #     'uint:' + str(defines.CODE_BITS) + '=code,' \
        #     'uint:' + str(defines.MESSAGE_ID_BITS) + '=mid'
        # d = {'version': defines.VERSION,
        #      'type': message.type,
        #      'code': message.code,
        #      'mid': message.mid}
        # if message.token is None or message.token == "":
        #     d['tokenlen'] = 0
        # else:
        #     d['tokenlen'] = len(message.token)
        #
        # self._writer = pack(fmt, **d)
        #
        # if message.token is not None and len(message.token) > 0:
        #     fmt = 'bytes:' + str(len(message.token)) + '=token'
        #     d = {'token': message.token}
        #     self._writer.append(pack(fmt, **d))
        #
        # options = self.as_sorted_list(message.options)  # already sorted
        # lastoptionnumber = 0
        # for option in options:
        #
        #     # write 4-bit option delta
        #     optiondelta = option.number - lastoptionnumber
        #     optiondeltanibble = self.get_option_nibble(optiondelta)
        #     fmt = 'uint:' + str(defines.OPTION_DELTA_BITS) + '=delta'
        #     d = {'delta': optiondeltanibble}
        #     self._writer.append(pack(fmt, **d))
        #     # self._writer.write(optiondeltanibble, defines.OPTION_DELTA_BITS)
        #
        #     # write 4-bit option length
        #     optionlength = option.length
        #     optionlengthnibble = self.get_option_nibble(optionlength)
        #     fmt = 'uint:' + str(defines.OPTION_LENGTH_BITS) + '=len'
        #     d = {'len': optionlengthnibble}
        #     self._writer.append(pack(fmt, **d))
        #     # self._writer.write(optionlengthnibble, defines.OPTION_LENGTH_BITS)
        #
        #     # write extended option delta field (0 - 2 bytes)
        #     if optiondeltanibble == 13:
        #         fmt = 'uint:8=delta'
        #         d = {'delta': optiondelta - 13}
        #         self._writer.append(pack(fmt, **d))
        #         # self._writer.write(optiondelta - 13, 8)
        #     elif optiondeltanibble == 14:
        #         fmt = 'uint:16=delta'
        #         d = {'delta': optiondelta - 269}
        #         self._writer.append(pack(fmt, **d))
        #         # self._writer.write(optiondelta - 269, 16)
        #
        #     # write extended option length field (0 - 2 bytes)
        #     if optionlengthnibble == 13:
        #         fmt = 'uint:8=len'
        #         d = {'len': optionlength - 13}
        #         self._writer.append(pack(fmt, **d))
        #         # self._writer.write(optionlength - 13, 8)
        #     elif optionlengthnibble == 14:
        #         fmt = 'uint:16=len'
        #         d = {'len': optionlength - 269}
        #         self._writer.append(pack(fmt, **d))
        #         # self._writer.write(optionlength - 269, 16)
        #
        #     # write option value
        #     fmt = 'bytes:'+str(optionlength)+'=option'
        #     d = {'option': option.raw_value.tobytes()}
        #     self._writer.append(pack(fmt, **d))
        #     # self._writer.writeBytes(option.getValue())
        #
        #     # update last option number
        #     lastoptionnumber = option.number
        #
        # payload = message.payload
        # if isinstance(payload, dict):
        #     payload = payload.get("Payload")
        # if payload is not None and len(payload) > 0:
        #     # if payload is present and of non-zero length, it is prefixed by
        #     # an one-byte Payload Marker (0xFF) which indicates the end of
        #     # options and the start of the payload
        #     fmt = 'uint:8=marker, bytes:' + str(len(payload)) + '=payload'
        #     d = {'marker': str(defines.PAYLOAD_MARKER), 'payload': payload}
        #     self._writer.append(pack(fmt, **d))
        #
        # return self._writer.tobytes()
        fmt = "!BBH"

        if message.token is None or message.token == "":
            tkl = 0
        else:
            tkl = len(message.token)
        tmp = (defines.VERSION << 2)
        tmp |= message.type
        tmp <<= 4
        tmp |= tkl
        values = [tmp, message.code, message.mid]

        # self._writer = BitManipulationWriter()
        # self._writer.write_bits(defines.VERSION_BITS, defines.VERSION)
        # self._writer.write_bits(defines.TYPE_BITS, message.type)
        # self._writer.write_bits(defines.TOKEN_LENGTH_BITS, tkl)
        # self._writer.write_bits(defines.CODE_BITS, message.code)
        # self._writer.write_bits(defines.MESSAGE_ID_BITS, message.mid)
        if message.token is not None and len(message.token) > 0:
            for b in str(message.token):
                fmt += "c"
                values.append(b)

                # self._writer.write_bits(len(message.token) * 8, message.token)

        options = self.as_sorted_list(message.options)  # already sorted
        lastoptionnumber = 0
        for option in options:

            # write 4-bit option delta
            optiondelta = option.number - lastoptionnumber
            optiondeltanibble = self.get_option_nibble(optiondelta)
            tmp = (optiondeltanibble << defines.OPTION_DELTA_BITS)

            # self._writer.write_bits(defines.OPTION_DELTA_BITS, optiondeltanibble)

            # write 4-bit option length
            optionlength = option.length
            optionlengthnibble = self.get_option_nibble(optionlength)
            tmp |= optionlengthnibble
            # self._writer.write_bits(defines.OPTION_LENGTH_BITS, optionlengthnibble)
            fmt += "B"
            values.append(tmp)

            # write extended option delta field (0 - 2 bytes)
            if optiondeltanibble == 13:
                # self._writer.write_bits(8, optiondelta - 13)
                fmt += "B"
                values.append(optiondelta - 13)
            elif optiondeltanibble == 14:
                # self._writer.write_bits(16, optiondelta - 296)
                fmt += "B"
                values.append(optiondelta - 296)

            # write extended option length field (0 - 2 bytes)
            if optionlengthnibble == 13:
                # self._writer.write_bits(8, optionlength - 13)
                fmt += "B"
                values.append(optionlength - 13)
            elif optionlengthnibble == 14:
                # self._writer.write_bits(16, optionlength - 269)
                fmt += "B"
                values.append(optionlength - 269)

            # write option value
            # self._writer.write_bits(optionlength * 8, option.value)
            name, opt_type, repeatable, defaults = defines.options[option.number]
            if optionlength == 1 and opt_type == defines.INTEGER:
                fmt += "B"
                values.append(option.value)
            elif optionlength == 2 and opt_type == defines.INTEGER:
                fmt += "H"
                values.append(option.value)
            else:
                for b in str(option.value):
                    fmt += "c"
                    values.append(b)

            # update last option number
            lastoptionnumber = option.number

        payload = message.payload
        if isinstance(payload, dict):
            payload = payload.get("Payload")
        if payload is not None and len(payload) > 0:
            # if payload is present and of non-zero length, it is prefixed by
            # an one-byte Payload Marker (0xFF) which indicates the end of
            # options and the start of the payload

            # self._writer.write_bits(8, defines.PAYLOAD_MARKER)
            fmt += "B"
            values.append(defines.PAYLOAD_MARKER)

            # self._writer.write_bits(len(payload) * 8, payload)
            for b in str(payload):
                fmt += "c"
                values.append(b)

        s = struct.Struct(fmt)
        self._writer = ctypes.create_string_buffer(s.size)
        s.pack_into(self._writer, 0, *values)
        return self._writer

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

    @staticmethod
    def as_sorted_list(options):
        """
        Returns all options in a list sorted according to their option numbers.

        :return: the sorted list
        """
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
            return bytearray()
        if isinstance(value, tuple):
            value = value[0]
        if isinstance(value, unicode):
            value = str(value)
        if isinstance(value, str):
            return bytearray(value, "utf-8")
        else:
            return bytearray(value)