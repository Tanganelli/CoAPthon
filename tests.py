# -*- coding: utf-8 -*-
import random
import socket
import threading
import unittest
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

    def tearDown(self):
        self.server.close()
        self.server_thread.join(timeout=25)
        self.server = None

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

    def test_retrasnmissions(self):
        print "Retransmissions"
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
        self._test_plugtest([(req, expected), (None, expected2), (None, expected2), (None, expected2)])

if __name__ == '__main__':
    unittest.main()
