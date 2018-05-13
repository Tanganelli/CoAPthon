from coapthon.client.helperclient import HelperClient


def main():
    host = "127.0.0.1"
    port = 5683
    client = HelperClient(server=(host, port))

    # Test discover
    # path = "/.well-known/core"
    # response = client.get(path)
    # print response.pretty_print()

    # registration test
    # path = "rd?ep=node1"
    # ct = {'content_type': 40}
    # payload = '</sensors/temp>;ct=41;rt="temperature-c";if="sensor";anchor="coap://spurious.example.com:5683",' \
    #          '</sensors/light>;ct=41;rt="light-lux";if="sensor"'
    # response = client.post(path, payload, None, None, **ct)
    # print response.pretty_print()

    # update test
    # path = "/rd/3"
    # response = client.post(path, '')
    # print response.pretty_print()

    # res lookup test
    # path = 'rd-lookup/res?ep=node1'
    # response = client.get(path)
    # print response.pretty_print()

    # read endpoint links
    # path = 'rd/1'
    # response = client.get(path)
    # print response.pretty_print()

    # ep lookup test
    # path = 'rd-lookup/ep?res=*'
    # response = client.get(path)
    # print response.pretty_print()

    # delete test
    # path = '/rd/5'
    # response = client.delete(path)
    # print response.pretty_print()

    client.stop()


if __name__ == '__main__':
    main()

