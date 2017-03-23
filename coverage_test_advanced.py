import threading
import unittest
from Queue import Queue
import random

from coapserver import CoAPServer
from coapthon import defines
from coapthon.client.helperclient import HelperClient
from coapthon.messages.option import Option
from coapthon.messages.request import Request
from coapthon.messages.response import Response


class Tests(unittest.TestCase):

    def setUp(self):
        self.server_address = ("127.0.0.1", 5683)
        self.current_mid = random.randint(1, 1000)
        self.server_mid = random.randint(1000, 2000)
        self.server = CoAPServer("127.0.0.1", 5683)
        self.server_thread = threading.Thread(target=self.server.listen, args=(10,))
        self.server_thread.start()
        self.queue = Queue()

    def tearDown(self):
        self.server.close()
        self.server_thread.join(timeout=25)
        self.server = None

    def _test_with_client(self, message_list):  # pragma: no cover
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
                if expected.options:
                    self.assertEqual(len(received_message.options), len(expected.options))
                    for o in expected.options:
                        assert isinstance(o, Option)
                        option_value = getattr(expected, o.name.lower().replace("-", "_"))
                        option_value_rec = getattr(received_message, o.name.lower().replace("-", "_"))
                        self.assertEqual(option_value, option_value_rec)
        client.stop()

    def client_callback(self, response):
        print "Callback"
        self.queue.put(response)

    def test_advanced(self):
        print "TEST_ADVANCED"
        path = "/advanced"
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
        expected.max_age = 20
        expected.token = None

        exchange1 = (req, expected)

        self.current_mid += 1

        req = Request()
        req.code = defines.Codes.POST.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.CREATED.number
        expected.payload = "Response changed through POST"
        expected.token = None

        exchange2 = (req, expected)

        self.current_mid += 1

        req = Request()
        req.code = defines.Codes.PUT.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.CHANGED.number
        expected.payload = "Response changed through PUT"
        expected.token = None

        exchange3 = (req, expected)

        self.current_mid += 1

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
        expected.payload = "Response deleted"
        expected.token = None

        exchange4 = (req, expected)

        self.current_mid += 1
        self._test_with_client([exchange1, exchange2, exchange3, exchange4])

    def test_advanced_separate(self):
        print "TEST_ADVANCED_SEPARATE"
        path = "/advancedSeparate"
        req = Request()
        req.code = defines.Codes.GET.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address

        expected = Response()
        expected.type = defines.Types["CON"]
        expected._mid = None
        expected.code = defines.Codes.CONTENT.number
        expected.max_age = 20
        expected.token = None

        exchange1 = (req, expected)

        self.current_mid += 1

        req = Request()
        req.code = defines.Codes.POST.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address

        expected = Response()
        expected.type = defines.Types["CON"]
        expected._mid = None
        expected.code = defines.Codes.CREATED.number
        expected.payload = "Response changed through POST"
        expected.token = None

        exchange2 = (req, expected)

        self.current_mid += 1

        req = Request()
        req.code = defines.Codes.PUT.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address

        expected = Response()
        expected.type = defines.Types["CON"]
        expected._mid = None
        expected.code = defines.Codes.CHANGED.number
        expected.payload = "Response changed through PUT"
        expected.token = None

        exchange3 = (req, expected)

        self.current_mid += 1

        req = Request()
        req.code = defines.Codes.DELETE.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address

        expected = Response()
        expected.type = defines.Types["CON"]
        expected._mid = None
        expected.code = defines.Codes.DELETED.number
        expected.payload = "Response deleted"
        expected.token = None

        exchange4 = (req, expected)

        self.current_mid += 1
        self._test_with_client([exchange1, exchange2, exchange3, exchange4])

if __name__ == '__main__':
    unittest.main()
