from distutils.core import setup

setup(
    name='CoAPthon',
    version='4.0.2',
    packages=['coapthon', 'coapthon.caching', 'coapthon.layers', 'coapthon.client', 'coapthon.server', 'coapthon.messages',
              'coapthon.forward_proxy', 'coapthon.resources', 'coapthon.reverse_proxy'],
    url='https://github.com/Tanganelli/CoAPthon',
    license='MIT License',
    author='Giacomo Tanganelli',
    author_email='giacomo.tanganelli@for.unipi.it',
    description='CoAPthon is a python library to the CoAP protocol. ',
    scripts=['coapserver.py', 'coapclient.py', 'exampleresources.py', 'coapforwardproxy.py', 'coapreverseproxy.py'],
    requires=['sphinx', 'cachetools', 'pymongo', 'dtls']
)
