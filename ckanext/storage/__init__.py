import os
from logging import getLogger

from ckan.plugins import implements, IConfigurer, IRoutes, SingletonPlugin

log = getLogger(__name__)


class Storage(SingletonPlugin):
    implements(IRoutes, inherit=True)
    implements(IConfigurer, inherit=True)

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
        # upload page
        route_map.connect('upload', '/upload',
            controller='ckanext.storage.controller:UploadController',
            action='index')
        route_map.connect('upload_success', '/upload/success',
            controller='ckanext.storage.controller:UploadController',
            action='success')
        route_map.connect('upload_error', '/upload/error',
            controller='ckanext.storage.controller:UploadController',
            action='error')
        return route_map

    def update_config(self, config):
        rootdir = os.path.dirname(__file__)
        our_public_dir = os.path.join(rootdir, 'public')
        template_dir = os.path.join(rootdir, 'templates')
        # config['extra_public_paths'] = ','.join([our_public_dir,
        #        config.get('extra_public_paths', '')])
        config['extra_template_paths'] = ','.join([template_dir,
                config.get('extra_template_paths', '')])

