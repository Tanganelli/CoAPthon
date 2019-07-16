from Queue import Queue
import random
import socket
import threading
import unittest
from coapclient import HelperClient
from coapforwardproxy import CoAPForwardProxy
from coapserver import CoAPServer
from coapthon import defines
from coapthon.messages.option import Option
from coapthon.messages.request import Request
from coapthon.messages.response import Response
from coapthon.serializer import Serializer
import time

__author__ = 'Emilio Vallati'
__version__ = "1.0"


class Tests(unittest.TestCase):

    def setUp(self):
        self.server_address = ("127.0.0.1", 5683)
        self.current_mid = random.randint(1, 1000)
        self.server_mid = random.randint(1000, 2000)
        self.server = CoAPServer("127.0.0.1", 5684)
        self.server_thread = threading.Thread(target=self.server.listen, args=(10,))
        self.server_thread.start()
        self.proxy = CoAPForwardProxy("127.0.0.1", 5683, cache=True)
        self.proxy_thread = threading.Thread(target=self.proxy.listen, args=(10,))
        self.proxy_thread.start()
        self.queue = Queue()

    def tearDown(self):
        self.server.close()
        self.server_thread.join(timeout=25)
        self.server = None
        self.proxy.close()
        self.proxy_thread.join(timeout=25)
        self.proxy = None

    def _test_with_client_delayed(self, message_list):  # pragma: no cover
        client = HelperClient(self.server_address)
        for message, expected in message_list:
            if message is not None:
                received_message = client.send_request(message)
                time.sleep(5)

            if expected is not None:
                if expected.etag is not None:
                    self.assertEqual(received_message.etag, expected.etag)
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
                if expected.max_age is not None:
                    if expected.max_age != 60:
                        self.assertNotEqual(received_message.max_age, 60)
                    else:
                        self.assertEqual(received_message.max_age, expected.max_age)
                if expected.options:
                    self.assertEqual(len(received_message.options), len(expected.options))
                    for o in expected.options:
                        assert isinstance(o, Option)
                        if o.name != defines.OptionRegistry.MAX_AGE.name and o.name != defines.OptionRegistry.ETAG.name:
                            option_value = getattr(expected, o.name.lower().replace("-", "_"))
                            option_value_rec = getattr(received_message, o.name.lower().replace("-", "_"))
                            self.assertEqual(option_value, option_value_rec)
        client.stop()

    def client_callback(self, response):
        print "Callback"
        self.queue.put(response)

    def test_get_multiple(self):
        print "TEST_GET_MULTIPLE"
        path = "/basic"
        req = Request()
        req.code = defines.Codes.GET.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.proxy_uri = "coap://127.0.0.1:5684/basic"

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.CONTENT.number
        expected.token = None
        expected.payload = "Basic Resource"

        exchange1 = (req, expected)

        self.current_mid += 1

        # PREPARING SECOND EXPECTED RESPONSE (MAX AGE MUST BE CHECKED)
        req2 = Request()
        req2.code = defines.Codes.GET.number
        req2.uri_path = path
        req2.type = defines.Types["CON"]
        req2._mid = self.current_mid
        req2.destination = self.server_address
        req2.proxy_uri = "coap://127.0.0.1:5684/basic"

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.CONTENT.number
        expected.token = None
        expected.payload = "Basic Resource"
        expected.max_age = 61

        exchange2 = (req2, expected)

        self._test_with_client_delayed([exchange1, exchange2])

    def test_get_post(self):
        print "TEST_GET_POST"
        path = "/basic"
        req = Request()
        req.code = defines.Codes.POST.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.proxy_uri = "coap://127.0.0.1:5684/storage/new"
        req.payload = "Hello"

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.CREATED.number
        expected.token = None
        expected.payload = None

        exchange1 = (req, expected)

        self.current_mid += 1

        # PREPARING SECOND EXPECTED RESPONSE
        req2 = Request()
        req2.code = defines.Codes.GET.number
        req2.uri_path = path
        req2.type = defines.Types["CON"]
        req2._mid = self.current_mid
        req2.destination = self.server_address
        req2.proxy_uri = "coap://127.0.0.1:5684/storage/new"

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.CONTENT.number
        expected.token = None
        expected.payload = "Hello"

        exchange2 = (req2, expected)

        self.current_mid += 1

        # PREPARING THIRD EXPECTED RESPONSE
        req3 = Request()
        req3.code = defines.Codes.POST.number
        req3.uri_path = path
        req3.type = defines.Types["CON"]
        req3._mid = self.current_mid
        req3.destination = self.server_address
        req3.proxy_uri = "coap://127.0.0.1:5684/storage/new"
        req3.payload = "Hello"

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.CREATED.number
        expected.token = None
        expected.payload = None

        exchange3 = (req3, expected)

        self.current_mid += 1

        # PREPARING FOURTH EXPECTED RESPONSE
        req4 = Request()
        req4.code = defines.Codes.GET.number
        req4.uri_path = path
        req4.type = defines.Types["CON"]
        req4._mid = self.current_mid
        req4.destination = self.server_address
        req4.proxy_uri = "coap://127.0.0.1:5684/storage/new"

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.CONTENT.number
        expected.token = None
        expected.payload = "Hello"

        exchange4 = (req4, expected)

        self.current_mid += 1

        self._test_with_client_delayed([exchange1, exchange2, exchange3, exchange4])

    def test_get_put(self):
        print "TEST_GET_PUT"
        path = "/basic"
        req = Request()
        req.code = defines.Codes.POST.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.proxy_uri = "coap://127.0.0.1:5684/storage/new"
        req.payload = "Hello"

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.CREATED.number
        expected.token = None
        expected.payload = None

        exchange1 = (req, expected)

        self.current_mid += 1

        # PREPARING SECOND EXPECTED RESPONSE
        req2 = Request()
        req2.code = defines.Codes.GET.number
        req2.uri_path = path
        req2.type = defines.Types["CON"]
        req2._mid = self.current_mid
        req2.destination = self.server_address
        req2.proxy_uri = "coap://127.0.0.1:5684/storage/new"

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.CONTENT.number
        expected.token = None
        expected.payload = "Hello"

        exchange2 = (req2, expected)

        self.current_mid += 1

        # PREPARING THIRD EXPECTED RESPONSE
        req3 = Request()
        req3.code = defines.Codes.PUT.number
        req3.uri_path = path
        req3.type = defines.Types["CON"]
        req3._mid = self.current_mid
        req3.destination = self.server_address
        req3.proxy_uri = "coap://127.0.0.1:5684/storage/new"
        req3.payload = "Hello"

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.CHANGED.number
        expected.token = None
        expected.payload = None

        exchange3 = (req3, expected)

        self.current_mid += 1

        # PREPARING FOURTH EXPECTED RESPONSE
        req4 = Request()
        req4.code = defines.Codes.GET.number
        req4.uri_path = path
        req4.type = defines.Types["CON"]
        req4._mid = self.current_mid
        req4.destination = self.server_address
        req4.proxy_uri = "coap://127.0.0.1:5684/storage/new"

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.CONTENT.number
        expected.token = None
        expected.payload = "Hello"

        exchange4 = (req4, expected)

        self.current_mid += 1

        self._test_with_client_delayed([exchange1, exchange2, exchange3, exchange4])

    def test_get_delete(self):
        print "TEST_GET_DELETE"
        path = "/basic"

        req2 = Request()
        req2.code = defines.Codes.GET.number
        req2.uri_path = path
        req2.type = defines.Types["CON"]
        req2._mid = self.current_mid
        req2.destination = self.server_address
        req2.proxy_uri = "coap://127.0.0.1:5684/storage/new"

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.NOT_FOUND.number
        expected.token = None
        expected.payload = None

        exchange0 = (req2, expected)

        self.current_mid += 1

        req = Request()
        req.code = defines.Codes.POST.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.proxy_uri = "coap://127.0.0.1:5684/storage/new"
        req.payload = "Hello"

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.CREATED.number
        expected.token = None
        expected.payload = None

        exchange1 = (req, expected)

        self.current_mid += 1

        # PREPARING SECOND EXPECTED RESPONSE
        req2 = Request()
        req2.code = defines.Codes.GET.number
        req2.uri_path = path
        req2.type = defines.Types["CON"]
        req2._mid = self.current_mid
        req2.destination = self.server_address
        req2.proxy_uri = "coap://127.0.0.1:5684/storage/new"

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.CONTENT.number
        expected.token = None
        expected.payload = "Hello"

        exchange2 = (req2, expected)

        self.current_mid += 1

        # PREPARING THIRD EXPECTED RESPONSE
        req3 = Request()
        req3.code = defines.Codes.DELETE.number
        req3.uri_path = path
        req3.type = defines.Types["CON"]
        req3._mid = self.current_mid
        req3.destination = self.server_address
        req3.proxy_uri = "coap://127.0.0.1:5684/storage/new"

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.DELETED.number
        expected.token = None
        expected.payload = None

        exchange3 = (req3, expected)

        self.current_mid += 1

        # PREPARING FOURTH EXPECTED RESPONSE
        req4 = Request()
        req4.code = defines.Codes.GET.number
        req4.uri_path = path
        req4.type = defines.Types["CON"]
        req4._mid = self.current_mid
        req4.destination = self.server_address
        req4.proxy_uri = "coap://127.0.0.1:5684/storage/new"

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.NOT_FOUND.number
        expected.token = None

        exchange4 = (req4, expected)

        self.current_mid += 1

        self._test_with_client_delayed([exchange0, exchange1, exchange2, exchange3, exchange4])

    def test_get_etag(self):
        print "TEST_GET_ETAG"
        path = "/etag"
        req = Request()
        req.code = defines.Codes.GET.number
        req.uri_path = path
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.proxy_uri = "coap://127.0.0.1:5684/etag"

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.CONTENT.number
        expected.token = None
        expected.payload = None
        expected.etag = str(0)

        exchange1 = (req, expected)

        self.current_mid += 1

        # PREPARING SECOND EXPECTED RESPONSE
        req2 = Request()
        req2.code = defines.Codes.GET.number
        req2.uri_path = path
        req2.type = defines.Types["CON"]
        req2._mid = self.current_mid
        req2.destination = self.server_address
        req2.proxy_uri = "coap://127.0.0.1:5684/etag"

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.CONTENT.number
        expected.token = None
        expected.etag = str(0)
        expected.max_age = 1

        exchange2 = (req2, expected)

        self.current_mid += 1

        # PREPARING THIRD EXPECTED RESPONSE
        req3 = Request()
        req3.code = defines.Codes.POST.number
        req3.uri_path = path
        req3.type = defines.Types["CON"]
        req3._mid = self.current_mid
        req3.destination = self.server_address
        req3.proxy_uri = "coap://127.0.0.1:5684/etag"
        req3.payload = "Hello"

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.CHANGED.number
        expected.token = None
        expected.payload = None
        expected.etag = str(1)
        expected.location_path = "etag"

        exchange3 = (req3, expected)

        self.current_mid += 1

        # PREPARING FOURTH EXPECTED RESPONSE
        req4 = Request()
        req4.code = defines.Codes.GET.number
        req4.uri_path = path
        req4.type = defines.Types["CON"]
        req4._mid = self.current_mid
        req4.destination = self.server_address
        req4.proxy_uri = "coap://127.0.0.1:5684/etag"

        expected = Response()
        expected.type = defines.Types["ACK"]
        expected._mid = self.current_mid
        expected.code = defines.Codes.CONTENT.number
        expected.token = None
        expected.payload = "Hello"
        expected.etag = str(1)

        exchange4 = (req4, expected)

        self.current_mid += 1

        self._test_with_client_delayed([exchange1, exchange2, exchange3, exchange4])


if __name__ == '__main__':
    unittest.main()
