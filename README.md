[![Build Status](https://travis-ci.org/Tanganelli/CoAPthon.svg?branch=master)](https://travis-ci.org/Tanganelli/CoAPthon)
CoAPthon
========

CoAPthon is a python library to the CoAP protocol compliant with the RFC.
Branch is available for the Twisted framework.

Citation
--------

If you use CoAPthon software in your research, please cite: 

G.Tanganelli, C. Vallati, E.Mingozzi, "CoAPthon: Easy Development of CoAP-based IoT Applications with Python", IEEE World Forum on Internet of Things (WF-IoT 2015)

Software available at https://github.com/Tanganelli/CoAPthon

What is implemented
===================

- CoAP server
- CoAP client asynchronous/synchronous
- CoAP to CoAP Forwarding proxy
- CoAP to CoAP Reverse Proxy
- Observe feature
- CoRE Link Format parsing
- Multicast server discovery
- Blockwise feature

TODO
====

- CoAP to HTTP Proxy
- DTLS support

Install instructions
=============
To install the library you need the pip program:

Debian/Ubuntu

```sh
$ sudo apt-get install python-pip
```

Fedora/CentOS

```sh
$ sudo yum install python-pip
```
Archlinux
```sh
$ sudo pacman -S python-pip
```

Once you have the pip program issue the following commands:

```sh
$ cd CoAPthon
$ python setup.py sdist
$ sudo pip install dist/CoAPthon-4.0.0.tar.gz -r requirements.txt
```

The library is installed in the default path as well as the bins that you can use and customize. In order to start
the example CoAP server issue:

```sh
$ coapserver.py
```

To uninstall:
-------------

```sh
$ sudo pip uninstall CoAPthon
```

Install instructions on Arduino Yun
======

Log through ssh to the Yun and issue the following:
```sh
# opkg update #updates the available packages list
# opkg install distribute #it contains the easy_install command line tool
# opkg install python-openssl #adds ssl support to python
# easy_install pip #installs pip
```

Then you need to modify the setup.py and comment the line <strong>conditionalExtensions=getExtensions()</strong>. Then :

```sh
# python setup.py build_py build_scripts install --skip-build
```

User Guide
========

CoAP server
-----------
In order to implements a CoAP server the basic class must be extended. Moreover the server must add some resources.

```Python
from coapthon.server.coap import CoAP
from exampleresources import BasicResource

class CoAPServer(CoAP):
    def __init__(self, host, port):
        CoAP.__init__(self, (host, port))
        self.add_resource('basic/', BasicResource())

def main():
    server = CoAPServer("127.0.0.1", 5683)
    try:
        server.listen(10)
    except KeyboardInterrupt:
        print "Server Shutdown"
        server.close()
        print "Exiting..."

if __name__ == '__main__':
    main()
```

Resources are extended from the class resource.Resource. Simple examples can be found in example_resource.py.

```Python
from coapthon.resources.resource import Resource

class BasicResource(Resource):
    def __init__(self, name="BasicResource", coap_server=None):
        super(BasicResource, self).__init__(name, coap_server, visible=True,
                                            observable=True, allow_children=True)
        self.payload = "Basic Resource"

    def render_GET(self, request):
        return self

    def render_PUT(self, request):
        self.payload = request.payload
        return self

    def render_POST(self, request):
        res = BasicResource()
        res.location_query = request.uri_query
        res.payload = request.payload
        return res

    def render_DELETE(self, request):
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