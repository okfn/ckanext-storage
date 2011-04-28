import re

from ofs import get_impl
from pylons import request, response
from pylons.controllers.util import abort, redirect_to

from ckan.lib.base import BaseController
from ckan.lib.jsonp import jsonpify

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
            'auth/request/{bucket}/{label}': {
                'description': 'Get authorization key valid for 15m',
                'methods': ['GET', 'POST']
                },
            'auth/form/{bucket}/{label}': {
                'description': 'Get authorization key valid for 15m',
                'methods': ['GET', 'POST']
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
    
    @jsonpify
    def get_metadata(self, bucket, label):
        if not label.startswith("/"): label = "/" + label
        if not self.ofs.exists(bucket, label):
            abort(404)
        metadata = self.ofs.get_metadata(bucket, label)
        url = "https://%s/%s%s" % (self.ofs.conn.server_name(), bucket, label)
        metadata["_location"] = url
        return metadata

    def _authorize(self, method, bucket, key):
        # TODO: implement
        pass

    @jsonpify
    def auth_request(self, bucket, label):
        '''Provide authentication information for a request so a client can
        interact with backend storage directly.

        :param bucket: bucket name.
        :param label: label.
        :param kwargs: sent either via query string for GET or json-encoded
            dict for POST). Interpreted as http headers for request plus an
            (optional) method parameter (being the HTTP method).

            Examples of headers are:

                Content-Type
                Content-Encoding (optional)
                Content-Length
                Content-MD5
                Expect (should be '100-Continue')

        :return: is a json hash containing various attributes including a
        headers dictionary containing an Authorization field which is good for
        15m.
        '''
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
        if 'method' in headers:
            method = headers['method']
            del headers['method']
        else:
            method = 'POST'

        self._authorize(method, bucket, label)
            
        http_request = self.ofs.authenticate_request(method, bucket, label,
                headers)
        return {
            'host': http_request.host,
            'method': http_request.method,
            'path': http_request.path,
            'headers': http_request.headers
            }

    @jsonpify
    def auth_form(self, bucket, label):
        '''Provide fields for a form upload to storage including
        authentication.

        :param bucket: bucket name.
        :param label: label.
        :param kwargs: sent either via query string for GET or json-encoded
            dict for POST. Possible key values are as for arguments to this
            underlying method:
            http://boto.cloudhackers.com/ref/s3.html?highlight=s3#boto.s3.connection.S3Connection.build_post_form_args

        :return: json-encoded dictionary with action parameter and fields list.
        '''
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

        self._authorize('POST', bucket, label)
            
        return self.ofs.conn.build_post_form_args(
            bucket,
            label,
            **headers
            )

