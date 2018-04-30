from coap import CoAP
from registration import Registration
from lookup import Lookup
from lookupRes import LookupRes
from lookupEp import LookupEp

__author__ = 'Carmelo Aparo'


class ResourceDirectory(CoAP):
    def __init__(self, host, port):
        CoAP.__init__(self, (host, port))
        self.add_resource('rd/', Registration())
        self.add_resource('rd-lookup/', Lookup())
        self.add_resource('rd-lookup/res', LookupRes())
        self.add_resource('rd-lookup/ep', LookupEp())
