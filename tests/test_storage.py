import os
from paste.deploy import appconfig
import paste.fixture
from ckan.config.middleware import make_app
import ckan.model as model
from ckan.tests import conf_dir, url_for, CreateTestData
from ckanext.admin.controller import get_sysadmins

class TestStorageAPIController:
    @classmethod
    def setup_class(cls):
        config = appconfig('config:test.ini', relative_to=conf_dir)
        config.local_conf['ckan.plugins'] = 'storage'
        config.local_conf['ofs.impl'] = 'pairtree'
        config.local_conf['ofs.storage_dir'] = '/tmp/ckan-test-ckanext-storage'
        wsgiapp = make_app(config.global_conf, **config.local_conf)
        cls.app = paste.fixture.TestApp(wsgiapp)

    def test_index(self):
        url = url_for('storage_api')
        res = self.app.get(url)
        out = res.json
        assert len(res.json) == 3

    def test_authz(self):
        url = url_for('storage_api_auth_form', label='abc')
        res = self.app.get(url, status=[302,401])


class TestStorageAPIControllerGoogle:
    @classmethod
    def setup_class(cls):
        config = appconfig('config:test.ini', relative_to=conf_dir)
        config.local_conf['ckan.plugins'] = 'storage'
        config.local_conf['ofs.impl'] = 'google'
        config.local_conf['ofs.gs_access_key_id'] = 'GOOGCABCDASDASD'
        config.local_conf['ofs.gs_secret_access_key'] = '134zsdfjkw4234addad'
        # need to ensure not configured for local as breaks google setup
        if 'ofs.storage_dir' in config.local_conf:
            del config.local_conf['ofs.storage_dir']
        wsgiapp = make_app(config.global_conf, **config.local_conf)
        cls.app = paste.fixture.TestApp(wsgiapp)
        # setup test data including testsysadmin user
        CreateTestData.create()
        model.Session.remove()
        user = model.User.by_name('tester')
        cls.extra_environ = {'Authorization': str(user.apikey)}

    @classmethod
    def teardown_class(cls):
        CreateTestData.delete()

    def test_auth_form(self):
        url = url_for('storage_api_auth_form', label='abc')
        res = self.app.get(url, extra_environ=self.extra_environ, status=200)
        assert res.json['fields'][-1]['value'] == 'abc', res

        url = url_for('storage_api_auth_form', label='abc/xxx')
        res = self.app.get(url, extra_environ=self.extra_environ, status=200)
        assert res.json['fields'][-1]['value'] == 'abc/xxx'

        url = url_for('storage_api_auth_form', label='abc',
                success_action_redirect='abc')
        res = self.app.get(url, extra_environ=self.extra_environ, status=200)
        fields = dict([ (x['name'], x['value']) for x in res.json['fields'] ])
        assert fields['success_action_redirect'] == u'http://localhost/api/storage/metadata/abc', fields

    def test_auth_request(self):
        url = url_for('storage_api_auth_request', label='abc')
        res = self.app.get(url, extra_environ=self.extra_environ, status=200)
        assert res.json['method'] == 'POST'
        assert res.json['headers']['Authorization']


class TestStorageAPIControllerLocal:
    @classmethod
    def setup_class(cls):
        config = appconfig('config:test.ini', relative_to=conf_dir)
        config.local_conf['ckan.plugins'] = 'storage'
        config.local_conf['ofs.impl'] = 'pairtree'
        config.local_conf['ofs.storage_dir'] = '/tmp/ckan-test-ckanext-storage'
        wsgiapp = make_app(config.global_conf, **config.local_conf)
        cls.app = paste.fixture.TestApp(wsgiapp)
        CreateTestData.create()
        model.Session.remove()
        user = model.User.by_name('tester')
        cls.extra_environ = {'Authorization': str(user.apikey)}

    @classmethod
    def teardown_class(cls):
        CreateTestData.delete()

    def test_auth_form(self):
        url = url_for('storage_api_auth_form', label='abc')
        res = self.app.get(url, extra_environ=self.extra_environ, status=200)
        assert res.json['action'] == u'http://localhost/storage/upload_handle', res.json
        assert res.json['fields'][-1]['value'] == 'abc', res

        url = url_for('storage_api_auth_form', label='abc/xxx')
        res = self.app.get(url, extra_environ=self.extra_environ, status=200)
        assert res.json['fields'][-1]['value'] == 'abc/xxx'

