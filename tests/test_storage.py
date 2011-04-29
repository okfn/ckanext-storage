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
        config.local_conf['ofs.impl'] = 'google'
        config.local_conf['ofs.gs_access_key_id'] = 'GOOGCABCDASDASD'
        config.local_conf['ofs.gs_secret_access_key'] = '134zsdfjkw4234addad'
        wsgiapp = make_app(config.global_conf, **config.local_conf)
        cls.app = paste.fixture.TestApp(wsgiapp)
        # setup test data including testsysadmin user
        CreateTestData.create()
        model.Session.remove()
        user = model.User.by_name('tester')
        cls.extra_environ = {'Authorization': str(user.apikey)}

    @classmethod
    def teardown_class(self):
        CreateTestData.delete()

    def test_index(self):
        url = url_for('storage_api')
        res = self.app.get(url)
        out = res.json
        assert len(res.json) == 3

    def test_authz(self):
        url = url_for('storage_api_auth_form', label='abc')
        res = self.app.get(url, status=[302,401])

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
        exp = {u'name': u'success_action_redirect', u'value': u'abc'}
        assert exp == res.json['fields'][0], res.json

    def test_auth_request(self):
        user = model.User.by_name('tester')
        url = url_for('storage_api_auth_request', label='abc')
        res = self.app.get(url, extra_environ=self.extra_environ, status=200)
        assert res.json['method'] == 'POST'
        assert res.json['headers']['Authorization']

