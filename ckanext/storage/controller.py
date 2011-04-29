import re
from datetime import datetime
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO
import urllib
import uuid
try:
    import json
except:
    import simplejson as json
from logging import getLogger

from ofs import get_impl
from pylons import request, response
from pylons.controllers.util import abort, redirect_to
from pylons import config

from ckan.lib.base import BaseController, c, request, render, config, h, abort
from ckan.lib.jsonp import jsonpify
import ckan.model as model
import ckan.authz as authz

log = getLogger(__name__)

storage_backend = config['ofs.impl']
BUCKET = config['ckanext.storage.bucket']
key_prefix = config.get('ckanext.storage.key_prefix', 'file/')


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

_eq_re = re.compile(r"^(.*)(=[0-9]*)$")
def fix_stupid_pylons_encoding(data):
    if data.startswith("%") or data.startswith("+"):
        data = urllib.unquote_plus(data)
    m = _eq_re.match(data)
    if m:
        data = m.groups()[0]
    return data

def get_ofs():
    kw = {}
    for k,v in config.items():
        if not k.startswith('ofs.') or k == 'ofs.impl':
            continue
        kw[k[4:]] = v
    ofs = get_impl(storage_backend)(**kw)
    return ofs

def authorize(method, bucket, key, user, ofs):
    if not method in ['POST', 'GET', 'PUT', 'DELETE']:
        abort(400)
    if method != 'GET':
        # do not allow overwriting
        if ofs.exists(bucket, key):
            abort(401)
        # now check user stuff
        username = user.name if user else ''
        is_authorized = authz.Authorizer.is_authorized(username, UPLOAD_ACTION, model.System()) 
        if not is_authorized:
            h.flash_error('Not authorized to upload files.')
            abort(401)


class StorageAPIController(BaseController):
    ofs = get_ofs()
    
    @jsonpify
    def index(self):
        info = {
            'metadata/{label}': {
                'description': 'Get or set metadata for this item in storage',
                },
            'auth/request/{label}': {
                'description': self.auth_request.__doc__,
                },
            'auth/form/{label}': {
                'description': self.auth_form.__doc__,
                }
            }
        return info

    def set_metadata(self, label):
        bucket = BUCKET
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
    def get_metadata(self, label):
        bucket = BUCKET
        if not label.startswith("/"): label = "/" + label
        if not self.ofs.exists(bucket, label):
            abort(404)
        metadata = self.ofs.get_metadata(bucket, label)
        url = "https://%s/%s%s" % (self.ofs.conn.server_name(), bucket, label)
        metadata["_location"] = url
        return metadata

    @jsonpify
    def auth_request(self, label):
        '''Provide authentication information for a request so a client can
        interact with backend storage directly.

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
        bucket = BUCKET
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

        authorize(method, bucket, label, c.userobj, self.ofs)
            
        http_request = self.ofs.authenticate_request(method, bucket, label,
                headers)
        return {
            'host': http_request.host,
            'method': http_request.method,
            'path': http_request.path,
            'headers': http_request.headers
            }

    @jsonpify
    def auth_form(self, label):
        '''Provide fields for a form upload to storage including
        authentication.

        :param label: label.
        :param kwargs: sent either via query string for GET or json-encoded
            dict for POST. Possible key values are as for arguments to this
            underlying method:
            http://boto.cloudhackers.com/ref/s3.html?highlight=s3#boto.s3.connection.S3Connection.build_post_form_args

        :return: json-encoded dictionary with action parameter and fields list.
        '''
        bucket = BUCKET
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

        method = 'POST'
        authorize(method, bucket, label, c.userobj, self.ofs)
        if 'max_content_length' in headers:
            headers['max_content_length'] = int(headers['max_content_length'])
            
        return self.ofs.conn.build_post_form_args(
            bucket,
            label,
            **headers
            )


class StorageController(BaseController):
    '''Upload to storage service (at the moment Google Developer storage.

    Required config:

    * ofs.gs_access_key_id
    * ofs.gs_secret_access_key
    * ofs.gs_bucket [optional]: the bucket to use for uploading (defaults to
      ckan)
    * ckanext.upload.max_content_length [optional]: maximum content size for
      uploads (defaults to 50Mb)
    '''
    ofs = get_ofs()

    def index(self):
        label = key_prefix + request.params.get('filepath', str(uuid.uuid4()))
        # would be nice to use filename of file
        # problem is 'we' don't know this at this point and cannot add it to
        # success_action_redirect and hence cannnot display to user afterwards
        # + '/${filename}'
        method = 'POST'
        authorize(method, BUCKET, label, c.userobj, self.ofs)

        content_length_range = int(
                config.get('ckanext.upload.max_content_length',
                    50000000))
        success_action_redirect = h.url_for('storage_upload_success', qualified=True,
                bucket=BUCKET, label=label)
        acl = 'public-read'
        fields = [ {
                'name': self.ofs.conn.provider.metadata_prefix + 'uploaded-by',
                'value': c.userobj.id
                }]
        conditions = [ '{"%s": "%s"}' % (x['name'], x['value']) for x in
                fields ]
        for f in fields:
            conditions.append
        c.data = self.ofs.conn.build_post_form_args(
            BUCKET,
            label,
            expires_in=600,
            max_content_length=content_length_range,
            success_action_redirect=success_action_redirect,
            acl=acl,
            fields=fields,
            conditions=conditions
            )
        # HACK: fix up some broken stuff from boto
        # e.g. should not have content-length-range in list of fields!
        for idx,field in enumerate(c.data['fields']):
            if storage_backend == 'google':
                if field['name'] == 'AWSAccessKeyId':
                    field['name'] = 'GoogleAccessId'
            if field['name'] == 'content-length-range':
                del c.data['fields'][idx]
        c.data_json = json.dumps(c.data, indent=2)
        return render('ckanext/storage/index.html')

    def success(self):
        h.flash_success('Upload successful')
        c.file_url = h.url_for('storage_file',
                label=request.params.get('label', ''),
                qualified=True
                )
        c.upload_url = h.url_for('storage_upload')
        return render('ckanext/storage/success.html')

    def file(self, label):
        url = self.ofs.get_url(BUCKET, label)
        h.redirect_to(url)

