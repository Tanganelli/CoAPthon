.. CoAPthon documentation master file, created by
   sphinx-quickstart on Mon Jun  2 18:08:28 2014.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to CoAPthon's documentation!
====================================

CoAPthon is a python library to the CoAP protocol aligned with 18th version of the draft.
It is based on the Twisted Framework.

.. toctree::
   :maxdepth: 2

.. highlight:: python
   :linenothreshold: 5

User Guide
==================

==================
CoAP Server
==================
In order to implements a CoAP server the basic class must be extended. Moreover the server must add some resources.

.. code-block:: python

    from twisted.internet import reactor
    from coapthon2.server.coap_protocol import CoAP
    from example_resources import Hello


    class CoAPServer(CoAP):
        def __init__(self):
            CoAP.__init__(self)
            self.add_resource('hello/', Hello())

    def main():
        reactor.listenUDP(5683, CoAPServer())
        reactor.run()


    if __name__ == '__main__':
        main()

Resources are extended from the :class:`resource.Resource`. Simple examples can be found in :mod:`example_resource.py`.

.. code-block:: python

    from coapthon2.resources.resource import Resource

    class Hello(Resource):
        def __init__(self, name="HelloResource"):
            super(Hello, self).__init__(name, visible=True, observable=True, allow_children=True)
            self.payload = "Hello world!"

        def render_GET(self, query=None):
            return self.payload

        def render_PUT(self, payload=None, query=None):
            return payload

        def render_POST(self, payload=None, query=None):
            q = "?" + "&".join(query)
            res = Hello()
            return {"Payload": payload, "Location-Query": q, "Resource": res}

        def render_DELETE(self, query=None):
            return True

Indices and tables
==================


:ref:`genindex`:
:emphasis:`Index of all functions`

:ref:`modindex`:
:emphasis:`Index of all modules`

:ref:`search`
:emphasis:`search this documentation`


