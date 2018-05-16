[![Build Status](https://travis-ci.org/Tanganelli/CoAPthon.svg?branch=master)](https://travis-ci.org/Tanganelli/CoAPthon)
[![Coverage Status](https://coveralls.io/repos/Tanganelli/CoAPthon/badge.svg?branch=master&service=github)](https://coveralls.io/github/Tanganelli/CoAPthon?branch=master)
[![Documentation Status](https://readthedocs.org/projects/coapthon/badge/?version=latest)](http://coapthon.readthedocs.org/en/latest/?badge=latest)

CoAPthon
========

CoAPthon is a python 2.7 library to the CoAP protocol compliant with the RFC.
Branch is available for the Twisted framework.

For python 3 please visit https://github.com/Tanganelli/CoAPthon3

Citation
--------

If you use CoAPthon software in your research, please cite: 

G.Tanganelli, C. Vallati, E.Mingozzi, "CoAPthon: Easy Development of CoAP-based IoT Applications with Python", IEEE World Forum on Internet of Things (WF-IoT 2015)

Software available at https://github.com/Tanganelli/CoAPthon

What is implemented
===================

- CoAP server
- CoAP client
- CoAP to CoAP Forward proxy
- CoAP to CoAP Reverse Proxy
- HTTP to CoAP Forward Proxy
- Caching feature
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

To install last release:
------------------------

```sh
$ sudo pip install CoAPthon
```

To install master branch:
-------------------------

```sh
$ git clone https://github.com/Tanganelli/CoAPthon.git
$ cd CoAPthon
$ python setup.py sdist
$ sudo pip install dist/CoAPthon-4.0.2.tar.gz -r requirements.txt
```

Running:
--------
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

Install instructions for CoRE Resource Directory
======

To use Resource Directory functionalities, you need to install mongoDB database [following the official documentation](https://docs.mongodb.com/manual/installation/).

Then you need to configure Resource Directory database. [Start mongod process](https://docs.mongodb.com/manual/tutorial/manage-mongodb-processes/) and [open a mongo shell](https://docs.mongodb.com/manual/mongo/). In mongo shell use these commands:

```sh
> use resourceDirectory
> db.createUser( {user: "RD",pwd: "res-dir",roles: [ { role: "readWrite", db: "resourceDirectory" } ] } )
> db.resources.createIndex( { "ep": 1, "d": 1 }, { unique: true } )
```

You can change user, password and database name in the commands above. If you change some parameters, then you must change them also in mongoDB parameters in coapthon/defines.py file where you will find also the path for your mongoDB configuration file. The default configuration file is /usr/local/etc/mongod.conf.

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
    server = CoAPServer("0.0.0.0", 5683)
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

Advanced Use
------------

### Separate Responses
 To always reply following the separate mode:
```Python
from coapthon.resources.resource import Resource

class Separate(Resource):

    def __init__(self, name="Separate", coap_server=None):
        super(Separate, self).__init__(name, coap_server, visible=True, observable=True, allow_children=True)
        self.payload = "Separate"
        self.max_age = 60

    def render_GET(self, request):
        return self, self.render_GET_separate

    def render_GET_separate(self, request):
        time.sleep(5)
        return self

    def render_POST(self, request):
        return self, self.render_POST_separate

    def render_POST_separate(self, request):
        self.payload = request.payload
        return self

    def render_PUT(self, request):
        return self, self.render_PUT_separate

    def render_PUT_separate(self, request):
        self.payload = request.payload
        return self

    def render_DELETE(self, request):
        return self, self.render_DELETE_separate

    def render_DELETE_separate(self, request):
        return True

```

### Advanced interface
Resources can be implemented also through a more advanced interface.

```Python
class AdvancedResource(Resource):
    def __init__(self, name="Advanced"):
        super(AdvancedResource, self).__init__(name)
        self.payload = "Advanced resource"

    def render_GET_advanced(self, request, response):
        response.payload = self.payload
        response.max_age = 20
        response.code = defines.Codes.CONTENT.number
        return self, response

    def render_POST_advanced(self, request, response):
        self.payload = request.payload
        from coapthon.messages.response import Response
        assert(isinstance(response, Response))
        response.payload = "Response changed through POST"
        response.code = defines.Codes.CREATED.number
        return self, response

    def render_PUT_advanced(self, request, response):
        self.payload = request.payload
        from coapthon.messages.response import Response
        assert(isinstance(response, Response))
        response.payload = "Response changed through PUT"
        response.code = defines.Codes.CHANGED.number
        return self, response

    def render_DELETE_advanced(self, request, response):
        response.payload = "Response deleted"
        response.code = defines.Codes.DELETED.number
        return True, response

```

### Separate mode with advanced interface

```Python
class AdvancedResourceSeparate(Resource):
    def __init__(self, name="Advanced"):
        super(AdvancedResourceSeparate, self).__init__(name)
        self.payload = "Advanced resource"

    def render_GET_advanced(self, request, response):
        return self, response, self.render_GET_separate

    def render_POST_advanced(self, request, response):
        return self, response, self.render_POST_separate

    def render_PUT_advanced(self, request, response):

        return self, response, self.render_PUT_separate

    def render_DELETE_advanced(self, request, response):
        return self, response, self.render_DELETE_separate

    def render_GET_separate(self, request, response):
        time.sleep(5)
        response.payload = self.payload
        response.max_age = 20
        return self, response

    def render_POST_separate(self, request, response):
        self.payload = request.payload
        response.payload = "Response changed through POST"
        return self, response

    def render_PUT_separate(self, request, response):
        self.payload = request.payload
        response.payload = "Response changed through PUT"
        return self, response

    def render_DELETE_separate(self, request, response):
        response.payload = "Response deleted"
        return True, response
```
CoAP client
-----------

```Python
from coapthon.client.helperclient import HelperClient

host = "127.0.0.1"
port = 5683
path ="basic"

client = HelperClient(server=(host, port))
response = client.get(path)
print response.pretty_print()
client.stop()
```

CoRE Resource Directory
------------

### Resource Directory server

You can start a CoRE Resource Directory server using ResourceDirectory class as follows:

```Python
from coapthon.resource_directory.resourceDirectory import ResourceDirectory


def main():
    server = ResourceDirectory("127.0.0.1", 5683)
    try:
        server.listen(10)
    except KeyboardInterrupt:
        print "Server Shutdown"
        server.close()
        print "Exiting..."


if __name__ == '__main__':
    main()
```

### Resource Directory client examples

```Python
def main():
    host = "127.0.0.1"
    port = 5683
    client = HelperClient(server=(host, port))

    # Test discover
    path = "/.well-known/core"
    response = client.get(path)
    print response.pretty_print()

    # Create a registration resource
    path = "rd?ep=node1&con=coap://local-proxy-old.example.com:5683&et=oic.d.sensor"
    ct = {'content_type': defines.Content_types["application/link-format"]}
    payload = '</sensors/temp>;ct=41;rt="temperature-c";if="sensor";anchor="coap://spurious.example.com:5683",' \
              '</sensors/light>;ct=41;rt="light-lux";if="sensor"'
    response = client.post(path, payload, None, None, **ct)
    location_path = response.location_path
    print response.pretty_print()

    # Resource lookup
    path = 'rd-lookup/res?if=sensor'
    response = client.get(path)
    print response.pretty_print()

    # Update a registration resource
    path = location_path + "?con=coaps://new.example.com:5684"
    response = client.post(path, '')
    print response.pretty_print()

    # Read endpoint links
    path = location_path
    response = client.get(path)
    print response.pretty_print()

    # Endpoint lookup
    path = 'rd-lookup/ep?et=oic.d.sensor'
    response = client.get(path)
    print response.pretty_print()

    # Delete a registration resource
    path = location_path
    response = client.delete(path)
    print response.pretty_print()

    client.stop()
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
