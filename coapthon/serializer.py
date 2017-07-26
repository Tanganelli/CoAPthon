import logging
import struct
import ctypes
from coapthon.messages.request import Request
from coapthon.messages.response import Response
from coapthon.messages.option import Option
from coapthon import defines
from coapthon.messages.message import Message

__author__ = 'Giacomo Tanganelli'

logger = logging.getLogger(__name__)


class Serializer(object):
    """
    Serializer class to serialize and deserialize CoAP message to/from udp streams.
    """
    @staticmethod
    def deserialize(datagram, source):
        """
        De-serialize a stream of byte to a message.

        :param datagram: the incoming udp message
        :param source: the source address and port (ip, port)
        :return: the message
        :rtype: Message
        """
        try:
            fmt = "!BBH"
            pos = struct.calcsize(fmt)
            s = struct.Struct(fmt)
            values = s.unpack_from(datagram)
            first = values[0]
            code = values[1]
            mid = values[2]
            version = (first & 0xC0) >> 6
            message_type = (first & 0x30) >> 4
            token_length = (first & 0x0F)
            if Serializer.is_response(code):
                message = Response()
                message.code = code
            elif Serializer.is_request(code):
                message = Request()
                message.code = code
            else:
                message = Message()
            message.source = source
            message.destination = None
            message.version = version
            message.type = message_type
            message.mid = mid
            if token_length > 0:
                fmt = "%ss" % token_length
                s = struct.Struct(fmt)
                token_value = s.unpack_from(datagram[pos:])[0]
                message.token = token_value
            else:
                message.token = None

            pos += token_length
            current_option = 0
            values = datagram[pos:]
            length_packet = len(values)
            pos = 0
            while pos < length_packet:
                next_byte = struct.unpack("B", values[pos])[0]
                pos += 1
                if next_byte != int(defines.PAYLOAD_MARKER):
                    # the first 4 bits of the byte represent the option delta
                    # delta = self._reader.read(4).uint
                    num, option_length, pos = Serializer.read_option_value_len_from_byte(next_byte, pos, values)
                    current_option += num
                    # read option
                    try:
                        option_item = defines.OptionRegistry.LIST[current_option]
                    except KeyError:
                        (opt_critical, _, _) = defines.OptionRegistry.get_option_flags(current_option)
                        if opt_critical:
                            raise AttributeError("Critical option %s unknown" % current_option)
                        else:
                            # If the non-critical option is unknown
                            # (vendor-specific, proprietary) - just skip it
                            #log.err("unrecognized option %d" % current_option)
                            pass
                    else:
                        if option_length == 0:
                            value = None
                        elif option_item.value_type == defines.INTEGER:
                            tmp = values[pos: pos + option_length]
                            value = 0
                            for b in tmp:
                                value = (value << 8) | struct.unpack("B", b)[0]
                        elif option_item.value_type == defines.OPAQUE:
                            tmp = values[pos: pos + option_length]
                            value = bytearray(tmp)
                        else:
                            tmp = values[pos: pos + option_length]
                            value = ""
                            for b in tmp:
                                value += str(b)

                        option = Option()
                        option.number = current_option
                        option.value = Serializer.convert_to_raw(current_option, value, option_length)

                        message.add_option(option)
                        if option.number == defines.OptionRegistry.CONTENT_TYPE.number:
                            message.payload_type = option.value
                    finally:
                        pos += option_length
                else:

                    if length_packet <= pos:
                        # log.err("Payload Marker with no payload")
                        raise AttributeError("Packet length %s, pos %s" % (length_packet, pos))
                    message.payload = ""
                    payload = values[pos:]
                    for b in payload:
                        message.payload += str(b)
                        pos += 1
            return message
        except AttributeError:
            return defines.Codes.BAD_REQUEST.number
        except struct.error:
            return defines.Codes.BAD_REQUEST.number

    @staticmethod
    def serialize(message):
        """
        Serialize a message to a udp packet

        :type message: Message
        :param message: the message to be serialized
        :rtype: stream of byte
        :return: the message serialized
        """
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

        if message.token is not None and tkl > 0:

            for b in str(message.token):
                fmt += "c"
                values.append(b)

        options = Serializer.as_sorted_list(message.options)  # already sorted
        lastoptionnumber = 0
        for option in options:

            # write 4-bit option delta
            optiondelta = option.number - lastoptionnumber
            optiondeltanibble = Serializer.get_option_nibble(optiondelta)
            tmp = (optiondeltanibble << defines.OPTION_DELTA_BITS)

            # write 4-bit option length
            optionlength = option.length
            optionlengthnibble = Serializer.get_option_nibble(optionlength)
            tmp |= optionlengthnibble
            fmt += "B"
            values.append(tmp)

            # write extended option delta field (0 - 2 bytes)
            if optiondeltanibble == 13:
                fmt += "B"
                values.append(optiondelta - 13)
            elif optiondeltanibble == 14:
                fmt += "H"
                values.append(optiondelta - 269)

            # write extended option length field (0 - 2 bytes)
            if optionlengthnibble == 13:
                fmt += "B"
                values.append(optionlength - 13)
            elif optionlengthnibble == 14:
                fmt += "H"
                values.append(optionlength - 269)

            # write option value
            if optionlength > 0:
                opt_type = defines.OptionRegistry.LIST[option.number].value_type
                if opt_type == defines.INTEGER:
                    words = Serializer.int_to_words(option.value, optionlength, 8)
                    for num in range(0, optionlength):
                        fmt += "B"
                        values.append(words[num])
                elif opt_type == defines.STRING:
                    for b in str(option.value):
                        fmt += "c"
                        values.append(b)
                else:
                    for b in option.value:
                        fmt += "B"
                        values.append(b)


            # update last option number
            lastoptionnumber = option.number

        payload = message.payload

        if payload is not None and len(payload) > 0:
            # if payload is present and of non-zero length, it is prefixed by
            # an one-byte Payload Marker (0xFF) which indicates the end of
            # options and the start of the payload

            fmt += "B"
            values.append(defines.PAYLOAD_MARKER)

            for b in str(payload):
                fmt += "c"
                values.append(b)

        datagram = None
        if values[1] is None:
            values[1] = 0
        try:
            s = struct.Struct(fmt)
            datagram = ctypes.create_string_buffer(s.size)
            s.pack_into(datagram, 0, *values)
        except struct.error:
            # The .exception method will report on the exception encountered
            # and provide a traceback.
            logging.exception('Failed to pack structure')

        return datagram

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

    @staticmethod
    def read_option_value_from_nibble(nibble, pos, values):
        """
        Calculates the value used in the extended option fields.

        :param nibble: the 4-bit option header value.
        :return: the value calculated from the nibble and the extended option value.
        """
        if nibble <= 12:
            return nibble, pos
        elif nibble == 13:
            tmp = struct.unpack("!B", values[pos])[0] + 13
            pos += 1
            return tmp, pos
        elif nibble == 14:
            s = struct.Struct("!H")
            tmp = s.unpack_from(values[pos:])[0] + 269
            pos += 2
            return tmp, pos
        else:
            raise AttributeError("Unsupported option nibble " + str(nibble))

    @staticmethod
    def read_option_value_len_from_byte(byte, pos, values):
        """
        Calculates the value and length used in the extended option fields.

        :param byte: 1-byte option header value.
        :return: the value and length, calculated from the header including the extended fields.
        """
        h_nibble = (byte & 0xF0) >> 4
        l_nibble = byte & 0x0F
        value = 0
        length = 0
        if h_nibble <= 12:
            value = h_nibble
        elif h_nibble == 13:
            value = struct.unpack("!B", values[pos])[0] + 13
            pos += 1
        elif h_nibble == 14:
            s = struct.Struct("!H")
            value = s.unpack_from(values[pos:])[0] + 269
            pos += 2
        else:
            raise AttributeError("Unsupported option number nibble " + str(h_nibble))

        if l_nibble <= 12:
            length = l_nibble
        elif l_nibble == 13:
            length = struct.unpack("!B", values[pos])[0] + 13
            pos += 1
        elif l_nibble == 14:
            length = s.unpack_from(values[pos:])[0] + 269
            pos += 2
        else:
            raise AttributeError("Unsupported option length nibble " + str(l_nibble))
        return value, length, pos

    @staticmethod
    def convert_to_raw(number, value, length):
        """
        Get the value of an option as a ByteArray.

        :param number: the option number
        :param value: the option value
        :param length: the option length
        :return: the value of an option as a BitArray
        """

        opt_type = defines.OptionRegistry.LIST[number].value_type

        if length == 0 and opt_type != defines.INTEGER:
            return bytearray()
        if length == 0 and opt_type == defines.INTEGER:
            return 0
        if isinstance(value, tuple):
            value = value[0]
        if isinstance(value, unicode):
            value = str(value)
        if isinstance(value, str):
            return bytearray(value, "utf-8")
        elif isinstance(value, int):
            return value
        else:
            return bytearray(value)

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
            raise AttributeError("Unsupported option delta " + optionvalue)

    @staticmethod
    def int_to_words(int_val, num_words=4, word_size=32):
        """
        Convert a int value to bytes.

        :param int_val: an arbitrary length Python integer to be split up.
            Network byte order is assumed. Raises an IndexError if width of
            integer (in bits) exceeds word_size * num_words.

        :param num_words: number of words expected in return value tuple.

        :param word_size: size/width of individual words (in bits).

        :return: a list of fixed width words based on provided parameters.
        """
        max_int = 2 ** (word_size*num_words) - 1
        max_word_size = 2 ** word_size - 1

        if not 0 <= int_val <= max_int:
            raise AttributeError('integer %r is out of bounds!' % hex(int_val))

        words = []
        for _ in range(num_words):
            word = int_val & max_word_size
            words.append(int(word))
            int_val >>= word_size
        words.reverse()

        return words
