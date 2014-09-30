from distutils.core import setup

setup(
    name='CoAPthon',
    version='2.0.0',
    packages=['test', 'coapthon2', 'coapthon2.layer', 'coapthon2.client', 'coapthon2.server', 'coapthon2.messages',
              'coapthon2.resources'],
    url='https://github.com/Tanganelli/CoAPthon',
    license='GPL',
    author='Giacomo Tanganelli',
    author_email='giacomo.tanganelli@for.unipi.it',
    description='CoAPthon is a python library to the CoAP protocol aligned with 18th version of the draft. '
                'It is based on the Twisted Framework.',
    scripts=['coapserver.py', 'coapclient.py', 'example_resources.py', 'coapforwardproxy.py', 'coapreverseproxy.py',
             'reverse_proxy_mapping.xml'], requires=['twisted', 'sphinx', 'bitstring', 'futures']
)
