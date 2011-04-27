import os
from paste.deploy import appconfig
import paste.fixture
from ckan.config.middleware import make_app
import ckan.model as model
from ckan.tests import conf_dir, url_for, CreateTestData
from ckanext.admin.controller import get_sysadmins


class TestStorageController:
    @classmethod
    def setup_class(cls):
        config = appconfig('config:test.ini', relative_to=conf_dir)
        config.local_conf['ckan.plugins'] = 'storage'
        config.local_conf['ofs.impl'] = 'google'
        config.local_conf['ofs.gs_access_key_id'] = 'GOOGCABCDASDASD'
        config.local_conf['ofs.gs_secret_access_key'] = '134zsdfjkw4234addad'
        wsgiapp = make_app(config.global_conf, **config.local_conf)
        cls.app = paste.fixture.TestApp(wsgiapp)
        # setup test data including testsysadmin user
        CreateTestData.create()

    @classmethod
    def teardown_class(self):
        CreateTestData.delete()

    def test_index(self):
        url = url_for('storage')
        res = self.app.get(url)
        out = res.json
        assert len(res.json) == 2

