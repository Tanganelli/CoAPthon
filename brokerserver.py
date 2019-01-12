from coapthon.server.coap import CoAP
from coapthon.resources.PsResource import PsResource
import sys

"""
    Main server class for the Broker application
"""
class CoAPServer(CoAP):
    def __init__(self, host, port):	
        CoAP.__init__(self, (host, port))
        # Add the first base API ps/ resource
        self.add_resource('ps/', PsResource("PsResource",self))

def main():
    print("[BROKER] Starting Broker")
    sys.stdout.flush()    
    server = CoAPServer("0.0.0.0", 5683)
    try:
        server.listen(10)
    except KeyboardInterrupt:
        print "Server Shutdown"
        server.close()
        print "Exiting..."

if __name__ == '__main__':
    main()
