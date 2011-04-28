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

from ckan.plugins import implements, IConfigurable, IRoutes, SingletonPlugin

log = getLogger(__name__)


class Storage(SingletonPlugin):
    implements(IRoutes, inherit=True)
    
    def after_map(self, route_map):
        c = "ckanext.storage.controller:StorageController"
        route_map.connect('storage', "/api/storage", controller=c, action="index")
        route_map.connect("/api/storage/metadata/{bucket}/{label}", controller=c, action="set_metadata",
                          conditions={"method": ["PUT", "POST"]})
        route_map.connect("/api/storage/metadata/{bucket}/{label}", controller=c, action="get_metadata",
                          conditions={"method": ["GET"]})
        route_map.connect('storage_auth_request',
                "/api/storage/auth/request/{bucket}/{label:.*}",
                controller=c,
                action="auth_request"
                )
        route_map.connect('storage_auth_form',
                "/api/storage/auth/form/{bucket}/{label:.*}",
                controller=c,
                action="auth_form"
                )
        return route_map

