CoAPthon
========

CoAPthon is a python library to the CoAP protocol aligned with 18th version of the draft.
It is based on the Twisted Framework.

What is implemented
===================

- CoAP server
- CoAP client
- Observe feature
- CoRE Link Format parsing

TODO
====

- CoAP to CoAP Forwarding proxy
- CoAP to CoAP Reverse Proxy
- CoAP to HTTP Proxy
- Blockwise feature
- Multicast server discovery

Install instructions
=============
To install the library you need the pip program:

```sh
$ sudo apt-get install pip
```

Once you have the pip program issue the following commands:

```sh
$ cd CoAPthon
$ python setup.py sdist
$ sudo pip install dist/CoAPthon-2.0.0.tar.gz -r requirements.txt
```

The library is installed in the default path as well as the bins that you can use and customize. In order to start
the example CoAP server issue:

```sh
$ coapserver.py
```

To uninstall:

```sh
$ sudo pip uninstall CoAPthon
```

User Guide
========

CoAP server
-----------
In order to implements a CoAP server the basic class must be extended. Moreover the server must add some resources.

```Python
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
```

Resources are extended from the class resource.Resource. Simple examples can be found in example_resource.py.

```Python
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
```

Build the documentation
================
The documentation is based on the Sphinx framework. In order to build the documentation issue the following:

```sh
$ pip install Sphinx
$ cd CoAPthon/docs
$ make html
```

The documentation will be build in CoAPthon/docs/build/html. Let's start from index.html to have an overview of the library.