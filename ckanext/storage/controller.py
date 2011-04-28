import re
from datetime import datetime
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO
import urllib
from logging import getLogger

from ofs import get_impl
from pylons import request, response
from pylons.controllers.util import abort, redirect_to

from ckan.lib.base import BaseController
from ckan.lib.jsonp import jsonpify

log = getLogger(__name__)

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

import datetime
import base64
import hashlib
import hmac
import uuid
try:
    import json
except:
    import simplejson as json

from ckan.lib.base import BaseController, c, request, render, config, h, abort
import ckan.model as model
import ckan.authz as authz

UPLOAD_ACTION = u'file-upload'

def setup_permissions():
    '''Setup upload permissions if they do not already exist.
    '''
    uploadrole = u'file-uploader'
    existing = model.Session.query(model.RoleAction).filter_by(role=uploadrole).first()
    if existing:
        return
    action = model.RoleAction(role=uploadrole, action=UPLOAD_ACTION,
        context=u'')
    model.Session.add(action)
    visitor_roles = []
    logged_in_roles = [uploadrole]
    model.setup_user_roles(model.System(), visitor_roles, logged_in_roles, [])
    model.Session.commit()
    model.Session.remove()

# HACK! - should be a hook to do this on plugin install/initialize
# (this is inefficient as we will call it every time)
setup_permissions()


class UploadController(BaseController):
    '''Upload to storage service (at the moment Google Developer storage.

    Required config:

    * ofs.gs_access_key_id
    * ofs.gs_secret_access_key
    * ofs.gs_bucket [optional]: the bucket to use for uploading (defaults to
      ckan)
    * ckanext.upload.max_content_length [optional]: maximum content size for
      uploads (defaults to 50Mb)
    '''
    def index(self):
        is_authorized = authz.Authorizer.am_authorized(c, UPLOAD_ACTION, model.System()) 
        if not is_authorized:
            h.flash_error('Not authorized to upload files.')
            abort(401)


        c.bucket = config.get('ofs.gs_bucket', 'ckan')
        c.post_url = 'https://commondatastorage.googleapis.com/' + c.bucket

        c.google_access_key_id = config.get('ofs.gs_access_key_id', '')
        secret_key = config.get('ofs.gs_secret_access_key', '')

        # generate a random filename
        filepath = request.params.get('filepath', str(uuid.uuid4()))
        c.key = filepath

        # default to 50Mb
        content_length_range = int(
                config.get('ckanext.upload.max_content_length',
                    50000000))
        # expire in 10m
        expiration = datetime.datetime.utcnow() + datetime.timedelta(0,600,0)
        expiration = expiration.replace(microsecond=0)
        expiration = expiration.isoformat()
        if not expiration.endswith('Z'):
            expiration += 'Z'

        c.acl = 'public-read'
        fileurl = c.post_url + '/' + c.key
        c.success_action_redirect = h.url_for('upload_success', qualified=True,
                fileurl=fileurl)
        c.success_action_status = '201'
        c.failure_action_redirect = h.url_for('upload_error', qualified=True)
        policy = {
            'expiration': expiration,
            'conditions': [
                {'key': c.key},
                {"acl": c.acl},
                {"success_action_redirect": c.success_action_redirect },
                # work around google bug
                # https://groups.google.com/group/gs-discussion/browse_thread/thread/9406dcdea19752b6?pli=1
                ["starts-with", "$failure_action_redirect",
                    c.failure_action_redirect ],
                ['content-length-range', 0, content_length_range]
            ]
        }
        c.policy = base64.b64encode(json.dumps(policy))
        signature = hmac.new(secret_key, c.policy, digestmod=hashlib.sha1)
        c.signature = base64.b64encode(signature.digest())
        return render('ckanext/storage/index.html')

    def success(self):
        h.flash_success('Upload successful')
        c.file_url = request.params.get('fileurl', '')
        c.upload_url = h.url_for('upload')
        return render('ckanext/storage/success.html')

    def fail(self):
        return 'Upload failed. Please go back and try again'

