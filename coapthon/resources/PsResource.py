from coapthon.resources.resource import Resource
from coapthon import defines
import re
import sys

__author__ = 'Federico Rossi'


"""
 Delete the entire subtree of a resource if it has children,
 by recursive iteration of the subtree of root root_resource.
 If base is true, the deletion will be performed by the calling
 method, otherwise the deletion will be performed by the function
"""
def delete_subtree(root_resource,base=False):
    if(len(root_resource.children) == 0):
        print("[BROKER] Deleting: "+root_resource.name)
        root_resource.cs.remove_resource(root_resource.name)
        return
    for l in root_resource.children:
        delete_subtree(l)
        print("[BROKER] Removing from children: "+l.name)
        root_resource.children.remove(l)
    	if(len(root_resource.children) == 0 and not base):
        	print("[BROKER] Deleting: "+root_resource.name)
        	root_resource.cs.remove_resource(root_resource.name)
        	return        



"""
Base resource for the Publish/Subsribe topic.
Follows the Composite Design Pattern to maintain a recursive list 
of children.
"""
class PsResource(Resource):
    def __init__(self, name="PsResource",coap_server=None):
        super(PsResource, self).__init__(name, coap_server, visible=True,
                                            observable=True, allow_children=True)
        self.cs = coap_server
        self.resource_type = "core.ps" # draft stabdard
        self.content_type = "text/plain"
        self.payload = ""
        self.children = []

    """
        Handle get requests: observe requests are internally served
        by CoAPthon itself. 
    """
    def render_GET_advanced(self, request, response): 
        print(self.content_type);
        sys.stdout.flush();           
        response.payload = self.payload
        response.code = defines.Codes.CONTENT.number
        if(request.observe == 0): # Log observe biding
            host, port = request.source
            print("[BROKER] Binding observe to: "+host)
            sys.stdout.flush()    

        return self, response

    """
        Create a resource from the POST payload for the base url.
        Returns None if he request is BAD
        Returns another existant resource in case of duplicates
    """
    def createResFromPayload(self,payload,base):
        #RegEx to check if the format of the request is RFC compliant (also according to CoAPthon defines)
        if(payload is None or not re.match(r'^<(\w+)>;(?:(ct=\w+;)|(rt=\w+;)|(if=\w+;)|(sz=\w+;))+$',payload)):
            return None
        payload = payload[:-1]
        topicData = payload.split(";")
        topicPath = topicData[0]
        path = topicPath.replace("<","").replace(">","")
        for res in self.children:
            if(res.name == base+"/"+path):
                #RESROUCE ALREADY EXISTS
                return res
        # Create new Ps Resource with the new uri path
        resource = PsResource(base+"/"+path,self.cs)
        topicData.pop(0);
        attr = {}
        attr["obs"] = ""
        # Extract and build the attribute object for the new Resource
        for d in topicData:
            key,val = d.split("=")[0],d.split("=")[1]
            print("[BROKER] Attr: "+key+" Val:"+val)
            if(key == 'ct'):
                val = [val]
                print(val)
            attr[key] = val
        print(attr)
        resource.attributes = attr
        sys.stdout.flush()    
        return resource


    """
        Handle POST request to create resource on this path
    """
    def render_POST_advanced(self, request, response):
        child_res = self.createResFromPayload(request.payload,request.uri_path)
        # The request is not formatted according to RFC
        if(child_res is None):
            response.code = defines.Codes.BAD_REQUEST.number
            response.payload = "Bad Request"
            return self,response
        # The resource already exists at this topic
        if(child_res in self.children):
            response.code = defines.Codes.FORBIDDEN.number
            response.payload = child_res.name + " Already Exists"
            return self,response
        self.children.append(child_res)
        self.cs.add_resource(child_res.name,child_res)
        response.payload = child_res.name + " Created"
        response.code = defines.Codes.CREATED.number
        print("[BROKER] Resource "+child_res.name+" created.");
        sys.stdout.flush()            
        return self,response

    """
        Handle PUT requests to the resource
        - If resource exists it update the payload
        - Otherwise the modified internal implementation of CoAPthon creates
            a new resource
    """
    def render_PUT_advanced(self, request, response):
        print(request.uri_path)
        sys.stdout.flush()           
        # Forbid updating the base ps api resource         
        if(request.uri_path == "ps"):
            response.code = defines.Codes.FORBIDDEN.number
            response.payload = "Forbidden"
            return False, response        
        self.payload = request.payload
        print("[BROKER] "+self.name+" updated with content: "+request.payload)
        sys.stdout.flush()            
        # New resource has been created before passing control to this method
        if(response.code == defines.Codes.CREATED.number): 
            response.payload = "Created"
            return self,response
        response.payload = "Changed"
        response.code = defines.Codes.CHANGED.number
        return self, response

    """
        Handles resource DELETION as well as deletion 
        of possibly present children with a recursive deletion
    """
    def render_DELETE_advanced(self, request, response):
        if(request.uri_path == "ps"):
            response.code = defines.Codes.FORBIDDEN.number
            response.payload = "Forbidden"            
            return False, response
        response.payload = "Deleted"
        response.code = defines.Codes.DELETED.number
        print("[BROKER] Deleting subtree of "+self.name)
        sys.stdout.flush()    
        if(len(self.children)>0):
            delete_subtree(self,True)
        return True, response