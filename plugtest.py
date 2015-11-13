# -*- coding: utf-8 -*-
from Queue import Queue
import random
import socket
import threading
import unittest
from coapthon.messages.message import Message
from coapclient import HelperClient
from coapthon.messages.response import Response
from coapthon.messages.request import Request
from coapthon import defines
from coapthon.serializer import Serializer
from plugtest_coapserver import CoAPServerPlugTest

__author__ = 'Giacomo Tanganelli'
__version__ = "2.0"


class Tests(unittest.TestCase):

    def setUp(self):
        self.server_address = ("127.0.0.1", 5683)
        self.current_mid = random.randint(1, 1000)
        self.server_mid = random.randint(1000, 2000)
        self.server = CoAPServerPlugTest("127.0.0.1", 5683, starting_mid=self.server_mid)
        self.server_thread = threading.Thread(target=self.server.listen, args=(10,))
        self.server_thread.start()
        self.queue = Queue()

    def tearDown(self):
        self.server.close()
        self.server_thread.join(timeout=25)
        self.server = None

    def _test_with_client(self, message_list):
        client = HelperClient(self.server_address)
        for message, expected in message_list:
            if message is not None:
                received_message = client.send_request(message)
            if expected is not None:
                if expected.type is not None:
                    self.assertEqual(received_message.type, expected.type)
                if expected.mid is not None:
                    self.assertEqual(received_message.mid, expected.mid)
                self.assertEqual(received_message.code, expected.code)
                if expected.source is not None:
                    self.assertEqual(received_message.source, self.server_address)
                if expected.token is not None:
                    self.assertEqual(received_message.token, expected.token)
                if expected.payload is not None:
                    self.assertEqual(received_message.payload, expected.payload)
                if expected.options is not None:
                    self.assertEqual(received_message.options, expected.options)
        client.stop()

    def client_callback(self, response):
        print "Callback"
        self.queue.put(response)

    def _test_with_client_observe(self, message_list, callback):
        client = HelperClient(self.server_address)
        token = None
        last_mid = 0
        for message, expected in message_list:
            if message is not None:
                token = message.token
                client.send_request(message, callback)
            received_message = self.queue.get()
            if expected is not None:
                last_mid = expected.mid
                if expected.type is not None:
                    self.assertEqual(received_message.type, expected.type)
                if expected.mid is not None:
                    self.assertEqual(received_message.mid, expected.mid)
                self.assertEqual(received_message.code, expected.code)
                if expected.source is not None:
                    self.assertEqual(received_message.source, self.server_address)
                if expected.token is not None:
                    self.assertEqual(received_message.token, expected.token)
                if expected.payload is not None:
                    self.assertEqual(received_message.payload, expected.payload)
                if expected.options is not None:
                    self.assertEqual(received_message.options, expected.options)
        message = Message()
        message.type = defines.Types["RST"]
        message.token = token
        message._mid = last_mid
        message.destination = self.server_address
        client.send_empty(message)
        client.stop()

    def _test_plugtest(self, message_list):
        serializer = Serializer()
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        for message, expected in message_list:
            if message is not None:
                datagram = serializer.serialize(message)
                sock.sendto(datagram, message.destination)
            if expected is not None:
                datagram, source = sock.recvfrom(4096)
                received_message = serializer.deserialize(datagram, source)
                if expected.type is not None:
                    self.assertEqual(received_message.type, expected.type)
                if expected.mid is not None:
                    self.assertEqual(received_message.mid, expected.mid)
                self.assertEqual(received_message.code, expected.code)
                if expected.source is not None:
                    self.assertEqual(received_message.source, source)
                if expected.token is not None:
                    self.assertEqual(received_message.token, expected.token)
                if expected.payload is not None:
                    self.assertEqual(received_message.payload, expected.payload)
                if expected.options is not None:
                    self.assertEqual(received_message.options, expected.options)

        sock.close()

    def test_td_coap_link_01(self):
        print "TD_COAP_LINK_01"
        path = "/.well-known/core"
        req = Request()
        req.code = defines.Codes.GET.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.CONTENT.number
        expected.token = None
        expected.content_type = defines.Content_types["application/link-format"]
        expected.payload = """</separate>;</large-update>;</seg1/seg2/seg3>;rt="Type1",</large>;</seg1/seg2>;rt="Type1",</test>;rt="Type1",</obs>;</long>;</seg1>;rt="Type1",</query>;rt="Type1","""

        self.current_mid += 1
        self._test_with_client([(req, expected)])

    def test_td_coap_link_02(self):
        print "TD_COAP_LINK_02"
        path = "/.well-known/core"
        req = Request()
        req.code = defines.Codes.GET.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.uri_query = "rt=Type1"

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.CONTENT.number
        expected.token = None
        expected.content_type = defines.Content_types["application/link-format"]
        expected.payload = """</seg1/seg2/seg3>;rt="Type1",</seg1/seg2>;rt="Type1",</test>;rt="Type1",</seg1>;rt="Type1",</query>;rt="Type1","""

        self.current_mid += 1
        self._test_with_client([(req, expected)])

    def test_td_coap_core_01(self):
        print "TD_COAP_CORE_01"
        path = "/test"
        req = Request()
        req.code = defines.Codes.GET.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.CONTENT.number
        expected.token = None
        expected.payload = "Test Resource"

        self.current_mid += 1
        self._test_with_client([(req, expected)])

    def test_td_coap_core_02(self):
        print "TD_COAP_CORE_02"
        path = "/test_post"
        req = Request()

        req.code = defines.Codes.POST.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req.content_type = defines.Content_types["application/xml"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.payload = "<value>test</value>"

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.CREATED.number
        expected.token = None
        expected.payload = None
        expected.location_path = "/test_post"

        self.current_mid += 1
        self._test_with_client([(req, expected)])

    def test_td_coap_core_03(self):
        print "TD_COAP_CORE_03"
        path = "/test"
        req = Request()

        req.code = defines.Codes.PUT.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req.content_type = defines.Content_types["application/xml"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.payload = "<value>test</value>"

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.CHANGED.number
        expected.token = None
        expected.payload = None

        self.current_mid += 1
        exchange1 = (req, expected)

        req = Request()

        req.code = defines.Codes.GET.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.CONTENT.number
        expected.token = None
        expected.payload = "<value>test</value>"
        expected.content_type = defines.Content_types["application/xml"]

        self.current_mid += 1
        exchange2 = (req, expected)

        req = Request()

        req.code = defines.Codes.GET.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.accept = defines.Content_types["application/xml"]

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.CONTENT.number
        expected.token = None
        expected.payload = "<value>test</value>"
        expected.content_type = defines.Content_types["application/xml"]

        self.current_mid += 1
        exchange3 = (req, expected)
        self._test_with_client([exchange1, exchange2, exchange3])

    def test_td_coap_core_04(self):
        print "TD_COAP_CORE_04"
        path = "/test"
        req = Request()

        req.code = defines.Codes.DELETE.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.DELETED.number
        expected.token = None
        expected.payload = None

        self.current_mid += 1
        self._test_with_client([(req, expected)])

    def test_td_coap_core_05(self):
        print "TD_COAP_CORE_05"
        path = "/test"
        req = Request()

        req.code = defines.Codes.GET.number
        req.uri_path = path
        req.type = defines.Types["NON"]
        req._mid = self.current_mid
        req.destination = self.server_address

        expected = Response()
        expected.type = defines.Types["NON"]
        expected._mid = None
        expected.code = defines.Codes.CONTENT.number
        expected.token = None
        expected.payload = "Test Resource"

        self.current_mid += 1
        self._test_with_client([(req, expected)])

    def test_td_coap_core_06(self):
        print "TD_COAP_CORE_06"
        path = "/test_post"
        req = Request()

        req.code = defines.Codes.POST.number
        req.uri_path = path
        req.type = defines.Types["NON"]
        req.content_type = defines.Content_types["application/xml"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.payload = "<value>test</value>"

        expected = Response()
        expected.type = defines.Types["NON"]
        expected._mid = None
        expected.code = defines.Codes.CREATED.number
        expected.token = None
        expected.payload = None
        expected.location_path = "/test_post"

        self.current_mid += 1
        self._test_with_client([(req, expected)])

    def test_td_coap_core_07(self):
        print "TD_COAP_CORE_07"
        path = "/test"
        req = Request()

        req.code = defines.Codes.PUT.number
        req.uri_path = path
        req.type = defines.Types["NON"]
        req.content_type = defines.Content_types["application/xml"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.payload = "<value>test</value>"

        expected = Response()
        expected.type = defines.Types["NON"]
        expected._mid = None
        expected.code = defines.Codes.CHANGED.number
        expected.token = None
        expected.payload = None

        self.current_mid += 1
        self._test_with_client([(req, expected)])

    def test_td_coap_core_08(self):
        print "TD_COAP_CORE_08"
        path = "/test"
        req = Request()

        req.code = defines.Codes.DELETE.number
        req.uri_path = path
        req.type = defines.Types["NON"]
        req._mid = self.current_mid
        req.destination = self.server_address

        expected = Response()
        expected.type = defines.Types["NON"]
        expected._mid = None
        expected.code = defines.Codes.DELETED.number
        expected.token = None
        expected.payload = None

        self.current_mid += 1
        self._test_with_client([(req, expected)])

    def test_td_coap_core_09(self):
        print "TD_COAP_CORE_09"
        path = "/separate"
        req = Request()

        req.code = defines.Codes.GET.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = None
        expected.token = None
        expected.payload = None

        expected2 = Response()
        expected2.type = defines.Types["CON"]
        expected2._mid = self.server_mid
        expected2.code = defines.Codes.CONTENT.number
        expected2.token = None
        expected2.payload = "Separate Resource"

        self.current_mid += 1
        self._test_plugtest([(req, expected), (None, expected2)])

    def test_td_coap_core_10(self):
        print "TD_COAP_CORE_10"
        path = "/test"
        req = Request()

        req.code = defines.Codes.GET.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.token = "ciao"

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.CONTENT.number
        expected.token = None
        expected.payload = "Test Resource"
        expected.token = "ciao"

        self.current_mid += 1
        self._test_with_client([(req, expected)])

    def test_td_coap_core_12(self):
        print "TD_COAP_CORE_12"
        path = "/seg1/seg2/seg3"
        req = Request()

        req.code = defines.Codes.GET.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.CONTENT.number
        expected.payload = "Test Resource"

        self.current_mid += 1
        self._test_with_client([(req, expected)])

    def test_td_coap_core_13(self):
        print "TD_COAP_CORE_13"
        path = "/query?first=1&second=2&third=3"
        req = Request()

        req.code = defines.Codes.GET.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.CONTENT.number
        expected.token = None
        expected.payload = "Test Resource"

        self.current_mid += 1
        self._test_with_client([(req, expected)])

    def test_td_coap_obs_01(self):
        print "TD_COAP_OBS_01"
        path = "/obs"
        req = Request()

        req.code = defines.Codes.GET.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.observe = 0

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.CONTENT.number
        expected.token = None
        expected.payload = "Observable Resource"
        expected.observe = 1

        expected2 = Response()
        expected2.type = defines.Types["CON"]
        expected2._mid = self.server_mid
        expected2.code = defines.Codes.CONTENT.number
        expected2.token = None
        expected2.payload = "Observable Resource"
        expected2.observe = 1

        self.current_mid += 1
        self.server_mid += 1
        self._test_plugtest([(req, expected), (None, expected2)])

    def test_td_coap_obs_03(self):
        print "TD_COAP_OBS_03"
        path = "/obs"
        req = Request()

        req.code = defines.Codes.GET.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.observe = 0

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.CONTENT.number
        expected.token = None
        expected.payload = "Observable Resource"
        expected.observe = 1

        self.current_mid += 1

        expected2 = Response()
        expected2.type = defines.Types["CON"]
        expected2._mid = self.server_mid
        expected2.code = defines.Codes.CONTENT.number
        expected2.token = None
        expected2.payload = "Observable Resource"
        expected2.observe = 1

        rst = Response()
        rst.type = defines.Types["RST"]
        rst._mid = self.server_mid
        rst.code = defines.Codes.EMPTY.number
        rst.destination = self.server_address
        rst.token = None
        rst.payload = None

        self.current_mid += 1
        self.server_mid += 1
        self._test_plugtest([(req, expected), (None, expected2), (rst, None)])

    def test_td_coap_block_01(self):
        print "TD_COAP_BLOCK_01"
        path = "/large"

        req = Request()
        req.code = defines.Codes.GET.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.block2 = (0, 0, 1024)

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.CONTENT.number
        expected.token = None
        expected.payload = None
        expected.block2 = (0, 1, 1024)

        exchange1 = (req, expected)
        self.current_mid += 1
        self.server_mid += 1

        req = Request()
        req.code = defines.Codes.GET.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.block2 = (1, 0, 1024)

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.CONTENT.number
        expected.token = None
        expected.payload = None
        expected.block2 = (1, 0, 1024)

        exchange2 = (req, expected)
        self.current_mid += 1
        self.server_mid += 1

        self._test_plugtest([exchange1, exchange2])

    def test_td_coap_block_01_client(self):
        print "TD_COAP_BLOCK_01"
        path = "/large"

        req = Request()
        req.code = defines.Codes.GET.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = None
        req.destination = self.server_address
        req.block2 = (0, 0, 1024)

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = None
        expected.code = defines.Codes.CONTENT.number
        expected.token = None
        expected.payload = """"Me sabbee plenty"—grunted Queequeg, puffing away at his pipe and sitting up in bed.
"You gettee in," he added, motioning to me with his tomahawk, and throwing the clothes to one side. He really did this
in not only a civil but a really kind and charitable way. I stood looking at him a moment. For all his tattooings
he was on the whole a clean, comely looking cannibal. What's all this fuss I have been making about, thought I to
myself—the man's a human being just as I am: he has just as much reason to fear me, as I have to be afraid of him.
Better sleep with a sober cannibal than a drunken Christian.
"Landlord," said I, "tell him to stash his tomahawk there, or pipe, or whatever you call it; tell him to stop smoking,
in short, and I will turn in with him. But I don't fancy having a man smoking in bed with me. It's dangerous. Besides,
I ain't insured."
This being told to Queequeg, he at once complied, and again politely motioned me to get into bed—rolling over to one
side as much as to say—"I won't touch a leg of ye."
"Good night, landlord," said I, "you may go."
I turned in, and never slept better in my life.
Upon waking next morning about daylight, I found Queequeg's arm thrown over me in the most loving and affectionate
manner. You had almost thought I had been his wife. The counterpane was of patchwork, full of odd little
parti-coloured squares and triangles; and this arm of his tattooed all over with an interminable Cretan labyrinth
of a figure, no two parts of which were of one precise shade—owing I suppose to his keeping his arm at sea
unmethodically in sun and shade, his shirt sleeves irregularly rolled up at various times—this same arm of his,
I say, looked for all the world like a strip of that same patchwork quilt. Indeed, partly lying on it as the arm did
 when I first awoke, I could hardly tell it from the quilt, they so blended their hues together; and it was only by
 the sense of weight and pressure that I could tell that Queequeg was hugging"""
        expected.block2 = (1, 0, 1024)

        exchange1 = (req, expected)
        self.current_mid += 1
        self.server_mid += 1

        self._test_with_client([exchange1])

    def test_td_coap_block_02_client(self):
        print "TD_COAP_BLOCK_02"
        path = "/large"

        req = Request()
        req.code = defines.Codes.GET.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = None
        req.destination = self.server_address

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = None
        expected.code = defines.Codes.CONTENT.number
        expected.token = None
        expected.payload = """"Me sabbee plenty"—grunted Queequeg, puffing away at his pipe and sitting up in bed.
"You gettee in," he added, motioning to me with his tomahawk, and throwing the clothes to one side. He really did this
in not only a civil but a really kind and charitable way. I stood looking at him a moment. For all his tattooings
he was on the whole a clean, comely looking cannibal. What's all this fuss I have been making about, thought I to
myself—the man's a human being just as I am: he has just as much reason to fear me, as I have to be afraid of him.
Better sleep with a sober cannibal than a drunken Christian.
"Landlord," said I, "tell him to stash his tomahawk there, or pipe, or whatever you call it; tell him to stop smoking,
in short, and I will turn in with him. But I don't fancy having a man smoking in bed with me. It's dangerous. Besides,
I ain't insured."
This being told to Queequeg, he at once complied, and again politely motioned me to get into bed—rolling over to one
side as much as to say—"I won't touch a leg of ye."
"Good night, landlord," said I, "you may go."
I turned in, and never slept better in my life.
Upon waking next morning about daylight, I found Queequeg's arm thrown over me in the most loving and affectionate
manner. You had almost thought I had been his wife. The counterpane was of patchwork, full of odd little
parti-coloured squares and triangles; and this arm of his tattooed all over with an interminable Cretan labyrinth
of a figure, no two parts of which were of one precise shade—owing I suppose to his keeping his arm at sea
unmethodically in sun and shade, his shirt sleeves irregularly rolled up at various times—this same arm of his,
I say, looked for all the world like a strip of that same patchwork quilt. Indeed, partly lying on it as the arm did
 when I first awoke, I could hardly tell it from the quilt, they so blended their hues together; and it was only by
 the sense of weight and pressure that I could tell that Queequeg was hugging"""
        expected.block2 = (1, 0, 1024)

        exchange1 = (req, expected)
        self.current_mid += 1
        self.server_mid += 1

        self._test_with_client([exchange1])

    def test_td_coap_block_02(self):
        print "TD_COAP_BLOCK_02"
        path = "/large"

        req = Request()
        req.code = defines.Codes.GET.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.CONTENT.number
        expected.token = None
        expected.payload = None
        expected.block2 = (0, 1, 1024)

        exchange1 = (req, expected)
        self.current_mid += 1
        self.server_mid += 1

        req = Request()
        req.code = defines.Codes.GET.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.block2 = (1, 0, 1024)

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.CONTENT.number
        expected.token = None
        expected.payload = None
        expected.block2 = (1, 0, 1024)

        exchange2 = (req, expected)
        self.current_mid += 1
        self.server_mid += 1

        self._test_plugtest([exchange1, exchange2])

    def test_td_coap_block_03(self):
        print "TD_COAP_BLOCK_03"
        path = "/large-update"

        req = Request()
        req.code = defines.Codes.PUT.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.payload = """"Me sabbee plenty"—grunted Queequeg, puffing away at his pipe """
        req.block1 = (0, 1, 64)

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.CONTINUE.number
        expected.token = None
        expected.payload = None
        expected.block1 = (0, 1, 64)

        exchange1 = (req, expected)
        self.current_mid += 1
        self.server_mid += 1

        req = Request()
        req.code = defines.Codes.PUT.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.payload = """and sitting up in bed. "You gettee in," he added, motioning"""
        req.block1 = (1, 0, 64)

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.CHANGED.number
        expected.token = None
        expected.payload = None

        exchange2 = (req, expected)
        self.current_mid += 1
        self.server_mid += 1

        req = Request()
        req.code = defines.Codes.GET.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.CONTENT.number
        expected.token = None
        expected.payload = """"Me sabbee plenty"—grunted Queequeg, puffing away at his pipe and sitting up in bed. "You gettee in," he added, motioning"""

        exchange3 = (req, expected)
        self.current_mid += 1

        self._test_plugtest([exchange1, exchange2, exchange3])

    def test_duplicate(self):
        print "TEST_DUPLICATE"
        path = "/test"
        req = Request()
        req.code = defines.Codes.GET.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.CONTENT.number
        expected.token = None

        self.current_mid += 1
        self._test_plugtest([(req, expected), (req, expected)])

    def test_duplicate_not_completed(self):
        print "TEST_DUPLICATE_NOT_COMPLETED"
        path = "/long"
        req = Request()
        req.code = defines.Codes.GET.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = None
        expected.token = None

        expected2 = Response()
        expected2.type = defines.Types["CON"]
        expected2._mid = None
        expected2.code = defines.Codes.CONTENT.number
        expected2.token = None

        self.current_mid += 1
        self._test_plugtest([(req, None), (req, expected), (None, expected2)])

    def test_no_response(self):
        print "TEST_NO_RESPONSE"
        path = "/long"
        req = Request()
        req.code = defines.Codes.GET.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = None
        expected.token = None

        expected2 = Response()
        expected2.type = defines.Types["CON"]
        expected2._mid = None
        expected2.code = defines.Codes.CONTENT.number
        expected2.token = None

        self.current_mid += 1
        self._test_plugtest([(req, expected), (None, expected2), (None, expected2),  (None, expected2)])

    def test_edit_resource(self):
        print "TEST_EDIT_RESOURCE"
        path = "/obs"
        req = Request()

        req.code = defines.Codes.POST.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.payload = "<value>test</value>"

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.CREATED.number
        expected.token = None
        expected.payload = None
        expected.location_path = "/obs"

        self.current_mid += 1
        self._test_with_client([(req, expected)])

if __name__ == '__main__':
    unittest.main()
