# -*- coding: utf-8 -*-

"""
For examples on how to use CoAPthon with pyDTLS, please have a look at the methods below:

 - setUp()
 - test_ok_with_handshake_on_send()
 - test_ok_with_handshake_on_connect()
 - test_fail_with_handshake_on_send()
 - test_fail_with_handshake_on_connect()

"""
# System
import socket
import random
import threading
import unittest
import tempfile
import os

# Dtls
import ssl
from dtls.wrapper import wrap_server, wrap_client

# CoAPthon
from coapthon import defines
from coapthon.client.helperclient import HelperClient
from coapthon.server.coap import CoAP as CoAPServer
from coapthon.messages.option import Option
from coapthon.messages.request import Request
from coapthon.messages.response import Response
from exampleresources import Storage

# Logging
from logging import basicConfig, DEBUG, getLogger, root, Filter
basicConfig(level=DEBUG, format="%(asctime)s - %(threadName)-30s - %(name)s - %(levelname)s - %(message)s")


class Whitelist(Filter):
    def __init__(self, *whitelist):
        super(Filter, self).__init__()
        self.whitelist = [Filter(name) for name in whitelist]

    def filter(self, record):
        return any(f.filter(record) for f in self.whitelist)

for handler in root.handlers:
    handler.addFilter(Whitelist(__name__, 'coapthon'))
    # handler.addFilter(Whitelist(__name__, 'coapthon', 'dtls'))

_logger = getLogger(__name__)


__author__ = 'Björn Freise'


CA_CERT_VALID = """-----BEGIN CERTIFICATE-----
MIICCzCCAXQCCQCwvSKaN4J3cTANBgkqhkiG9w0BAQUFADBKMQswCQYDVQQGEwJV
UzETMBEGA1UECBMKV2FzaGluZ3RvbjETMBEGA1UEChMKUmF5IENBIEluYzERMA8G
A1UEAxMIUmF5Q0FJbmMwHhcNMTQwMTE4MjEwMjUwWhcNMjQwMTE2MjEwMjUwWjBK
MQswCQYDVQQGEwJVUzETMBEGA1UECBMKV2FzaGluZ3RvbjETMBEGA1UEChMKUmF5
IENBIEluYzERMA8GA1UEAxMIUmF5Q0FJbmMwgZ8wDQYJKoZIhvcNAQEBBQADgY0A
MIGJAoGBAN/UYXt4uq+YdTDnm7WPCu+0B50kJXWU3sSS+WAAhr3BHh7qa7UTiRXy
yGYysgvtwriETAZRckzd+hdblNRUWXGJdRvtyx94nLpPpI8p4djBrJ5IMPqK5SgW
ZP4XTWs694VtUBAvHCX+Ly+t0O5Rw3NmqxY1MakooqU9t+wL0H0TAgMBAAEwDQYJ
KoZIhvcNAQEFBQADgYEANemjvYCJrTc/6im0DmDC6AW8KrLG0xj31HWpq1dO9LG7
mlVFgbVtbcuCZgA78kxgw1vN6kBBLEsAJC8gkg++AO/w3a4oP+U9txAr9KRg6IGA
FiUohuWbjKBnQEpceoECgrymooF3ayzke/vf3wcMYy153uC+H4t96Yc5T066c4o=
-----END CERTIFICATE-----
"""

CA_CERT_WRONG = """-----BEGIN CERTIFICATE-----
MIIE6jCCBFOgAwIBAgIDEIGKMA0GCSqGSIb3DQEBBQUAME4xCzAJBgNVBAYTAlVT
MRAwDgYDVQQKEwdFcXVpZmF4MS0wKwYDVQQLEyRFcXVpZmF4IFNlY3VyZSBDZXJ0
aWZpY2F0ZSBBdXRob3JpdHkwHhcNMTAwNDAxMjMwMDE0WhcNMTUwNzAzMDQ1MDAw
WjCBjzEpMCcGA1UEBRMgMmc4YU81d0kxYktKMlpENTg4VXNMdkRlM2dUYmc4RFUx
CzAJBgNVBAYTAlVTMRMwEQYDVQQIEwpDYWxpZm9ybmlhMRIwEAYDVQQHEwlTdW5u
eXZhbGUxFDASBgNVBAoTC1lhaG9vICBJbmMuMRYwFAYDVQQDEw13d3cueWFob28u
Y29tMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA6ZM1jHCkL8rlEKse
1riTTxyC3WvYQ5m34TlFK7dK4QFI/HPttKGqQm3aVB1Fqi0aiTxe4YQMbd++jnKt
djxcpi7sJlFxjMZs4umr1eGo2KgTgSBAJyhxo23k+VpK1SprdPyM3yEfQVdV7JWC
4Y71CE2nE6+GbsIuhk/to+jJMO7jXx/430jvo8vhNPL6GvWe/D6ObbnxS72ynLSd
mLtaltykOvZEZiXbbFKgIaYYmCgh89FGVvBkUbGM/Wb5Voiz7ttQLLxKOYRj8Mdk
TZtzPkM9scIFG1naECPvCxw0NyMyxY3nFOdjUKJ79twanmfCclX2ZO/rk1CpiOuw
lrrr/QIDAQABo4ICDjCCAgowDgYDVR0PAQH/BAQDAgTwMB0GA1UdDgQWBBSmrfKs
68m+dDUSf+S7xJrQ/FXAlzA6BgNVHR8EMzAxMC+gLaArhilodHRwOi8vY3JsLmdl
b3RydXN0LmNvbS9jcmxzL3NlY3VyZWNhLmNybDCCAVsGA1UdEQSCAVIwggFOgg13
d3cueWFob28uY29tggl5YWhvby5jb22CDHVzLnlhaG9vLmNvbYIMa3IueWFob28u
Y29tggx1ay55YWhvby5jb22CDGllLnlhaG9vLmNvbYIMZnIueWFob28uY29tggxp
bi55YWhvby5jb22CDGNhLnlhaG9vLmNvbYIMYnIueWFob28uY29tggxkZS55YWhv
by5jb22CDGVzLnlhaG9vLmNvbYIMbXgueWFob28uY29tggxpdC55YWhvby5jb22C
DHNnLnlhaG9vLmNvbYIMaWQueWFob28uY29tggxwaC55YWhvby5jb22CDHFjLnlh
aG9vLmNvbYIMdHcueWFob28uY29tggxoay55YWhvby5jb22CDGNuLnlhaG9vLmNv
bYIMYXUueWFob28uY29tggxhci55YWhvby5jb22CDHZuLnlhaG9vLmNvbTAfBgNV
HSMEGDAWgBRI5mj5K9KylddH2CMgEE8zmJCf1DAdBgNVHSUEFjAUBggrBgEFBQcD
AQYIKwYBBQUHAwIwDQYJKoZIhvcNAQEFBQADgYEAp9WOMtcDMM5T0yfPecGv5QhH
RJZRzgeMPZitLksr1JxxicJrdgv82NWq1bw8aMuRj47ijrtaTEWXaCQCy00yXodD
zoRJVNoYIvY1arYZf5zv9VZjN5I0HqUc39mNMe9XdZtbkWE+K6yVh6OimKLbizna
inu9YTrN/4P/w6KzHho=
-----END CERTIFICATE-----
"""

KEY_CERT_VALID = """-----BEGIN PRIVATE KEY-----
MIICdgIBADANBgkqhkiG9w0BAQEFAASCAmAwggJcAgEAAoGBANjL+g7MpTEB40Vo
2pxWbx33YwgXQ6QbnLg1QyKlrH6DEEotyDRWI/ZftvWbjGUh0zUGhQaLzF3ZNgdM
VkF5j0wCgRdwPon1ct5wJUg6GCWvfi4B/HlQrWg8JDaWoGuDcTqLh6KYfDdWTlWC
Bq3pOW14gVe3d12R8Bxu9PCK8jrvAgMBAAECgYAQFjqs5HSRiWFS4i/uj99Y6uV3
UTqcr8vWQ2WC6aY+EP2hc3o6n/W1L28FFJC7ZGImuiAe1zrH7/k5W2m/HAUM7M9p
oBcp7ZVMFU6R00cQWVKCpQRCpNHnn+tVJdRGiHRj9836/u2z3shBxDYgXJIR787V
SlBXkCcsi0Clem5ocQJBAPp/0tF4CpoaOCAnNN+rDjPNGcH57lmpSZBMXZVAVCRq
vJDdH9SIcb19gKToCF1MUd7CJWbSHKxh49Hr+prBW8cCQQDdjrH8EZ4CDYvoJbVX
iWFfbh6lPwv8uaj43HoHq4+51mhHvLxO8a1AKMSgD2cg7yJYYIpTTAf21gqU3Yt9
wJeZAkEAl75e4u0o3vkLDs8xRFzGmbKg69SPAll+ap8YAZWaYwUVfVu2MHUHEZa5
GyxEBOB6p8pMBeE55WLXMw8UHDMNeQJADEWRGjMnm1mAvFUKXFThrdV9oQ2C7nai
I1ai87XO+i4kDIUpsP216O3ZJjx0K+DS+C4wuzhk4IkugNxck5SNUQJASxf8E4z5
W5rP2XXIohGpDyzI+criUYQ6340vKB9bPsCQ2QooQq1BH0wGA2fY82Kr95E8KhUo
zGoP1DtpzgwOQg==
-----END PRIVATE KEY-----
-----BEGIN CERTIFICATE-----
MIICDTCCAXYCCQCxc2uXBLZhDjANBgkqhkiG9w0BAQUFADBKMQswCQYDVQQGEwJV
UzETMBEGA1UECBMKV2FzaGluZ3RvbjETMBEGA1UEChMKUmF5IENBIEluYzERMA8G
A1UEAxMIUmF5Q0FJbmMwHhcNMTQwMTE4MjEwMjUwWhcNMjQwMTE2MjEwMjUwWjBM
MQswCQYDVQQGEwJVUzETMBEGA1UECBMKV2FzaGluZ3RvbjEUMBIGA1UEChMLUmF5
IFNydiBJbmMxEjAQBgNVBAMTCVJheVNydkluYzCBnzANBgkqhkiG9w0BAQEFAAOB
jQAwgYkCgYEA2Mv6DsylMQHjRWjanFZvHfdjCBdDpBucuDVDIqWsfoMQSi3INFYj
9l+29ZuMZSHTNQaFBovMXdk2B0xWQXmPTAKBF3A+ifVy3nAlSDoYJa9+LgH8eVCt
aDwkNpaga4NxOouHoph8N1ZOVYIGrek5bXiBV7d3XZHwHG708IryOu8CAwEAATAN
BgkqhkiG9w0BAQUFAAOBgQBw0XUTYzfiI0Fi9g4GuyWD2hjET3NtrT4Ccu+Jiivy
EvwhzHtVGAPhrV+VCL8sS9uSOZlmfK/ZVraDiFGpJLDMvPP5y5fwq5VGrFuZispG
X6bTBq2AIKzGGXxhwPqD8F7su7bmZDnZFRMRk2Bh16rv0mtzx9yHtqC5YJZ2a3JK
2g==
-----END CERTIFICATE-----
"""


class Tests(unittest.TestCase):

    def setUp(self):
        self.host_address = ("127.0.0.1", 5684)
        self.current_mid = random.randint(1, 1000)
        self.server_mid = random.randint(1000, 2000)
        self.server_read_timeout = 0.1

        self.pem = self._setUpPems()

        # Set up a server side DTLS socket
        _sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        _sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        _sock = wrap_server(_sock,
                            keyfile=self.pem['SERVER_KEY'],
                            certfile=self.pem['SERVER_KEY'],
                            ca_certs=self.pem['CA_CERT'])
        _sock.bind(self.host_address)
        _sock.listen(0)

        # Connect the CoAP server to the newly created socket
        self.server = CoAPServer(self.host_address,
                                 starting_mid=self.server_mid,
                                 sock=_sock,
                                 cb_ignore_listen_exception=self._cb_ignore_listen_exception)
        self.server.add_resource('storage/', Storage())

        # Test code to "pseudo" capture the udp communication between server and client on the loopback device
        try:
            from proxy import proxy_thread
            self.server_address, self.runFlag = proxy_thread(0, self.host_address[0], self.host_address[1])
        except ImportError:
            self.server_address = self.host_address
            self.runFlag = None

        # Start the server listen routine
        self.server_thread = threading.Thread(target=self.server.listen,
                                              name='ServerThread',
                                              args=(self.server_read_timeout,))
        self.server_thread.start()

    def tearDown(self):
        if self.runFlag is not None:
            self.runFlag.clear()

        # Stop the server from listening (also closes the socket)
        self.server.close()
        self.server_thread.join(timeout=self.server_read_timeout*1.2)
        self.server = None

        self._tearDownPems(self.pem)

    def _setUpPems(self):
        def _createPemFile(fname, content):
            with open(fname, mode='w') as f:
                f.write(content)
            f.close()
            return fname

        self._tmp_dir = tempfile.mkdtemp()

        pem = dict()
        pem['SERVER_KEY'] = _createPemFile(os.path.join(self._tmp_dir, 'serverkey.pem'), KEY_CERT_VALID)
        pem['CA_CERT'] = _createPemFile(os.path.join(self._tmp_dir, 'ca_cert.pem'), CA_CERT_VALID)
        pem['CA_CERT_WRONG'] = _createPemFile(os.path.join(self._tmp_dir, 'ca_cert_wrong.pem'), CA_CERT_WRONG)

        return pem

    def _tearDownPems(self, pem):
        def _removePemFile(fname):
            os.remove(fname)

        for v in pem.itervalues():
            _removePemFile(v)

        os.rmdir(self._tmp_dir)

    def _create_test_sequence(self, bValidResponse=True):
        exchange = list()
        req = Request()
        req.code = defines.Codes.POST.number
        req.uri_path = "/storage/new_res?id=1"
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.payload = "test"
        req.add_if_none_match()

        if bValidResponse:
            expected = Response()
            expected.type = defines.Types["ACK"]
            expected._mid = self.current_mid
            expected.code = defines.Codes.CREATED.number
            expected.token = None
            expected.payload = None
            expected.location_path = "storage/new_res"
            expected.location_query = "id=1"
        else:
            expected = None

        exchange.append((req, expected))
        self.current_mid += 1

        req = Request()
        req.code = defines.Codes.GET.number
        req.uri_path = "/storage/new_res"
        req.type = defines.Types["CON"]
        req._mid = self.current_mid
        req.destination = self.server_address
        req.if_match = ["test", "not"]

        if bValidResponse:
            expected = Response()
            expected.type = defines.Types["ACK"]
            expected._mid = self.current_mid
            expected.code = defines.Codes.CONTENT.number
            expected.token = None
            expected.payload = "test"
        else:
            expected = None

        exchange.append((req, expected))
        self.current_mid += 1

        return exchange

    def _test_with_client(self, client, message_list):  # pragma: no cover
        for message, expected in message_list:
            if message is not None:
                try:
                    received_message = client.send_request(message)
                except Exception as e:
                    if expected is not None:
                        self.assertEqual(None, expected)
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

    def _cb_ignore_listen_exception(self, exception, server):
        """
        In the CoAP server listen method, different exceptions can arise from the DTLS stack. Depending on the type of exception, a
        continuation might not be possible, or a logging might be desirable. With this callback both needs can be satisfied.

        :param exception: What happened inside the DTLS stack
        :param server: Reference to the running CoAP server
        :return: True if further processing should be done, False processing should be stopped
        """
        if isinstance(exception, ssl.SSLError):
            # A client which couldn't verify the server tried to connect, continue but log the event
            if exception.errqueue[-1][0] == ssl.ERR_TLSV1_ALERT_UNKNOWN_CA:
                _logger.debug("Ignoring ERR_TLSV1_ALERT_UNKNOWN_CA from client %s" %
                              ('unknown' if not hasattr(exception, 'peer') else str(exception.peer)))
                return True
            # ... and more ...
        return False

    def _cb_ignore_write_exception(self, exception, client):
        """
        In the CoAP client write method, different exceptions can arise from the DTLS stack. Depending on the type of exception, a
        continuation might not be possible, or a logging might be desirable. With this callback both needs can be satisfied.

        note: Default behaviour of CoAPthon without DTLS if no _cb_ignore_write_exception would be called is with "return True"

        :param exception: What happened inside the DTLS stack
        :param client: Reference to the running CoAP client
        :return: True if further processing should be done, False processing should be stopped
        """
        return False

    def _cb_ignore_read_exception(self, exception, client):
        """
        In the CoAP client read method, different exceptions can arise from the DTLS stack. Depending on the type of exception, a
        continuation might not be possible, or a logging might be desirable. With this callback both needs can be satisfied.

        note: Default behaviour of CoAPthon without DTLS if no _cb_ignore_read_exception would be called is with "return False"

        :param exception: What happened inside the DTLS stack
        :param client: Reference to the running CoAP client
        :return: True if further processing should be done, False processing should be stopped
        """
        return False

    def test_ok_with_handshake_on_send(self):
        """
        Test a valid CoAP sequence with DTLS encryption. The handshake is triggered from the client
        at its first write access towards the server.
        """
        _logger.info("Called test_ok_with_handshake_on_send ...")

        exchange = self._create_test_sequence()

        # Set up a client side DTLS socket
        _sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        _sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        _sock = wrap_client(_sock,
                            cert_reqs=ssl.CERT_REQUIRED,
                            ca_certs=self.pem['CA_CERT'],
                            ciphers="RSA",
                            do_handshake_on_connect=False)

        # Connect the CoAP client to the newly created socket
        client = HelperClient(self.server_address,
                              sock=_sock,
                              cb_ignore_read_exception=self._cb_ignore_read_exception,
                              cb_ignore_write_exception=self._cb_ignore_write_exception)

        # Do the communication
        try:
            self._test_with_client(client, exchange)
        except:
            raise
        # Stop the client (also closes the socket)
        finally:
            client.stop()

    def test_ok_with_handshake_on_connect(self):
        """
        Test a valid CoAP sequence with DTLS encryption. The handshake is triggered from the client
        during the connect call.
        """
        _logger.info("Called test_ok_with_handshake_on_connect ...")

        exchange = self._create_test_sequence()

        # Set up a client side DTLS socket
        _sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        _sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        _sock = wrap_client(_sock,
                            cert_reqs=ssl.CERT_REQUIRED,
                            ca_certs=self.pem['CA_CERT'],
                            ciphers="RSA",
                            do_handshake_on_connect=True)

        # Connect the CoAP client to the newly created socket
        client = HelperClient(self.server_address,
                              sock=_sock,
                              cb_ignore_read_exception=self._cb_ignore_read_exception,
                              cb_ignore_write_exception=self._cb_ignore_write_exception)

        # Do the communication
        try:
            self._test_with_client(client, exchange)
        except:
            raise
        # Stop the client (also closes the socket)
        finally:
            client.stop()

    def test_fail_with_handshake_on_send(self):
        """
        Test an invalid CoAP sequence with DTLS encryption. The handshake is triggered from the client
        at its first write access towards the server.
        """

        _logger.info("Called test_fail_with_handshake_on_send ...")

        exchange = self._create_test_sequence(bValidResponse=False)

        # Set up a client side DTLS socket
        _sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        _sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        _sock = wrap_client(_sock,
                            cert_reqs=ssl.CERT_REQUIRED,
                            ca_certs=self.pem['CA_CERT_WRONG'],
                            ciphers="RSA",
                            do_handshake_on_connect=False)

        # Connect the CoAP client to the newly created socket
        client = HelperClient(self.server_address,
                              sock=_sock,
                              cb_ignore_read_exception=self._cb_ignore_read_exception,
                              cb_ignore_write_exception=self._cb_ignore_write_exception)

        # Do the communication
        try:
            self._test_with_client(client, exchange)
        except:
            raise
        # Stop the client (also closes the socket)
        finally:
            client.stop()

    def test_fail_with_handshake_on_connect(self):
        """
        Test an invalid CoAP sequence with DTLS encryption. The handshake is triggered from the client
        during the connect call.
        """
        _logger.info("Called test_fail_with_handshake_on_connect ...")

        exchange = self._create_test_sequence(bValidResponse=False)

        # Set up a client side DTLS socket
        _sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        _sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        _sock = wrap_client(_sock,
                            cert_reqs=ssl.CERT_REQUIRED,
                            ca_certs=self.pem['CA_CERT_WRONG'],
                            ciphers="RSA",
                            do_handshake_on_connect=True)

        # Connect the CoAP client to the newly created socket
        client = HelperClient(self.server_address,
                              sock=_sock,
                              cb_ignore_read_exception=self._cb_ignore_read_exception,
                              cb_ignore_write_exception=self._cb_ignore_write_exception)

        # Do the communication
        try:
            self._test_with_client(client, exchange)
        except:
            raise
        # Stop the client (also closes the socket)
        finally:
            client.stop()


if __name__ == '__main__':
    unittest.main()
