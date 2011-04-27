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
from logging import getLogger

from ofs import get_impl
from pylons import request, response
from pylons.controllers.util import abort, redirect_to

from ckan.plugins import implements, IConfigurable, IRoutes, SingletonPlugin
from ckan.lib.base import BaseController

log = getLogger(__name__)


class Storage(SingletonPlugin):
    implements(IRoutes, inherit=True)
    
    def after_map(self, route_map):
        c = "ckanext.storage:StorageController"
        route_map.connect('storage', "/api/storage", controller=c, action="index")
        route_map.connect("/api/storage/metadata/{bucket}/{label}", controller=c, action="set_metadata",
                          conditions={"method": ["PUT", "POST"]})
        route_map.connect("/api/storage/metadata/{bucket}/{label}", controller=c, action="get_metadata",
                          conditions={"method": ["GET"]})
        route_map.connect('storage_auth_headers', "/api/storage/auth/{bucket}/{label:.*}", controller=c, action="get_headers",
                          conditions={"method": ["POST", "GET"]})
        route_map.connect('storage_auth_form',
                "/api/storage/auth_form/{bucket}/{label:.*}", controller=c,
                action="auth_form",
                          conditions={"method": ["POST", "GET"]})
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

from ckan.lib.jsonp import jsonpify
class StorageController(BaseController):
    @property
    def ofs(self):
        from pylons import config
        kw = {}
        for k,v in config.items():
            if not k.startswith('ofs.') or k == 'ofs.impl':
                continue
            kw[k[4:]] = v

        ofs = get_impl(config.get('ofs.impl', 'google'))(**kw)
        return ofs
    
    @jsonpify
    def index(self):
        info = {
            'metadata/{bucket}/{label}': {
                'description': 'Get or set metadata for this item in storage',
                'methods': ['GET', 'POST']
                },
            'auth/{bucket}/{label}': {
                'description': 'Get authorization key valid for 15m',
                'methods': ['POST', 'PUT']
                }
            }
        return info

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

    @jsonpify
    def get_headers(self, bucket, label):
        if request.POST:
            try:
                data = fix_stupid_pylons_encoding(request.body)
                headers = loads(data)
            except Exception, e:
                from traceback import print_exc
                msg = StringIO()
                print_exc(msg)
                log.error(msg.seek(0).read())
                abort(400)
        else:
            headers = dict(request.params)

        # TODO: authorization
            
        # does not existing boto 
        # self.ofs.conn.add_aws_auth_header(headers, 'PUT', "/" + bucket + label)
        # return (self.ofs.conn.server_name(), headers)
        return []

    @jsonpify
    def auth_form(self, bucket, label):
        if request.POST:
            try:
                data = fix_stupid_pylons_encoding(request.body)
                headers = loads(data)
            except Exception, e:
                from traceback import print_exc
                msg = StringIO()
                print_exc(msg)
                log.error(msg.seek(0).read())
                abort(400)
        else:
            headers = dict(request.params)

        # TODO: authorization
            
        return self.ofs.conn.build_post_form_args(
            bucket,
            label,
            **headers
            )

