from coapthon.client.helperclient import HelperClient
from coapthon import defines

__author__ = 'Carmelo Aparo'


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


if __name__ == '__main__':
    main()

