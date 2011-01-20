try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO
try:
    from json import dumps, loads
except ImportError:
    from simplejson import dumps, loads
from datetime import datetime
import urllib
from ofs import get_impl
from pylons import request, response
from pylons.controllers.util import abort, redirect_to
from ckan.plugins import implements, IConfigurable, IRoutes, SingletonPlugin
from ckan.lib.base import BaseController

class Storage(SingletonPlugin):
    implements(IConfigurable)
    implements(IRoutes)
    
    def configure(self, config):
        kw = {}
        for k,v in config.items():
            if not k.startswith('ofs.') or k == 'ofs.impl':
                continue
            kw[k[4:]] = v
        from ckanext import storage
        storage.ofs = get_impl(config.get('ofs.impl', 'google'))(**kw)

    def before_map(self, route_map):
        c = "ckanext.storage:StorageController"
        route_map.connect("/api/storage/metadata/:bucket/:label", controller=c, action="set_metadata",
                          conditions={"method": ["PUT", "POST"]})
        route_map.connect("/api/storage/metadata/:bucket/:label", controller=c, action="get_metadata",
                          conditions={"method": ["GET"]})
        route_map.connect("/api/storage/auth/:bucket/:label", controller=c, action="get_headers",
                          conditions={"method": ["POST"]})
        return route_map
    
    def after_map(self, route_map):
        return route_map

import re
_eq_re = re.compile(r"^(.*)(=[0-9]*)$")
def fix_stupid_pylons_encoding(data):
    if data.startswith("%") or data.startswith("+"):
        data = urllib.unquote_plus(data)
    m = _eq_re.match(data)
    if m:
        data = m.groups()[0]
    return data

class StorageController(BaseController):
    @property
    def ofs(self):
        from ckanext import storage
        return storage.ofs

    def set_metadata(self, bucket, label):
        if not label.startswith("/"): label = "/" + label

        try:
            data = fix_stupid_pylons_encoding(request.body)
            if data:
                metadata = loads(data)
            else:
                metadata = {}
        except:
            abort(400)
            
        try:
            b = self.ofs._require_bucket(bucket)
        except:
            abort(409)
            
        k = self.ofs._get_key(b, label)
        if k is None:
            k = b.new_key(label)
            metadata = metadata.copy()
            metadata["_creation_time"] = str(datetime.utcnow())
            self.ofs._update_key_metadata(k, metadata)
            k.set_contents_from_file(StringIO(''))
        elif request.method == "PUT":
            old = self.ofs.get_metadata(bucket, label)
            to_delete = []
            for ok in old.keys():
                if ok not in metadata:
                    to_delete.append(ok)
            if to_delete:
                self.ofs.del_metadata_keys(bucket, label, to_delete)
            self.ofs.update_metadata(bucket, label, metadata)
        else:
            self.ofs.update_metadata(bucket, label, metadata)            

        k.make_public()
        k.close()
        
        return self.get_metadata(bucket, label)
    
    def get_metadata(self, bucket, label):
        if not label.startswith("/"): label = "/" + label
        if not self.ofs.exists(bucket, label):
            abort(404)
        metadata = self.ofs.get_metadata(bucket, label)
        url = "https://%s/%s%s" % (self.ofs.conn.server_name(), bucket, label)
        metadata["_location"] = url
        return dumps(metadata)

    def get_headers(self, bucket, label):
        if not label.startswith("/"): label = "/" + label

        try:
            data = fix_stupid_pylons_encoding(request.body)
            headers = loads(data)
        except Exception, e:
            from traceback import print_exc
            print_exc()
            abort(400)

        if not self.ofs.exists(bucket, label):
            abort(404)
            
        if not headers:
            headers = {}
        self.ofs.conn.add_aws_auth_header(headers, 'PUT', "/" + bucket + label)
        return dumps((self.ofs.conn.server_name(), headers))
