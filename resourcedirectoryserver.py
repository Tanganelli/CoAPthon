from coapthon.resource_directory.resourceDirectory import ResourceDirectory
from coapthon import defines

__author__ = 'Carmelo Aparo'


def main():
    server = ResourceDirectory(defines.RD_HOST, defines.RD_PORT)
    try:
        server.listen(10)
    except KeyboardInterrupt:
        print "Server Shutdown"
        server.close()
        print "Exiting..."


if __name__ == '__main__':
    main()
