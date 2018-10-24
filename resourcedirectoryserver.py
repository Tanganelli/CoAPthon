from coapthon import defines
from coapthon.resource_directory.resourceDirectory import ResourceDirectory

__author__ = 'Carmelo Aparo'


def main():
    server = ResourceDirectory(defines.RD_HOST, defines.RD_PORT, start_mongo=False)
    try:
        server.listen(10)
    except KeyboardInterrupt:
        print "Server Shutdown"
        server.close()
        print "Exiting..."


if __name__ == '__main__':
    main()
