import os
from logging import getLogger

from ckan.plugins import implements, IConfigurer, IRoutes, SingletonPlugin

log = getLogger(__name__)


class Storage(SingletonPlugin):
    implements(IRoutes, inherit=True)
    implements(IConfigurer, inherit=True)

    def after_map(self, route_map):
        c = "ckanext.storage.controller:StorageAPIController"
        route_map.connect('storage_api', "/api/storage", controller=c, action="index")
        route_map.connect("/api/storage/metadata/{label:.*}", controller=c, action="set_metadata",
                          conditions={"method": ["PUT", "POST"]})
        route_map.connect("/api/storage/metadata/{label:.*}", controller=c, action="get_metadata",
                          conditions={"method": ["GET"]})
        route_map.connect('storage_api_auth_request',
                "/api/storage/auth/request/{label:.*}",
                controller=c,
                action="auth_request"
                )
        route_map.connect('storage_api_auth_form',
                "/api/storage/auth/form/{label:.*}",
                controller=c,
                action="auth_form"
                )
        # upload page
        route_map.connect('storage_upload', '/storage/upload',
            controller='ckanext.storage.controller:StorageController',
            action='index')
        route_map.connect('storage_upload_success', '/storage/upload/success',
            controller='ckanext.storage.controller:StorageController',
            action='success')
        route_map.connect('storage_file', '/storage/f/{label:.*}',
            controller='ckanext.storage.controller:StorageController',
            action='file')
        return route_map

    def update_config(self, config):
        rootdir = os.path.dirname(__file__)
        our_public_dir = os.path.join(rootdir, 'public')
        template_dir = os.path.join(rootdir, 'templates')
        # config['extra_public_paths'] = ','.join([our_public_dir,
        #        config.get('extra_public_paths', '')])
        config['extra_template_paths'] = ','.join([template_dir,
                config.get('extra_template_paths', '')])

