import os
from paste.deploy import appconfig
import paste.fixture

from ckan.config.middleware import make_app
from ckan.tests import conf_dir, url_for, CreateTestData
import ckan.model as model


class TestStatsPlugin:
    @classmethod
    def setup_class(cls):
        config = appconfig('config:test.ini', relative_to=conf_dir)
        config.local_conf['ckan.plugins'] = 'upload'
        wsgiapp = make_app(config.global_conf, **config.local_conf)
        cls.app = paste.fixture.TestApp(wsgiapp)
        CreateTestData.create()

    @classmethod
    def teardown_class(cls):
        model.Session.remove()
        model.repo.rebuild_db()

    def test_02_authorization(self):
        from ckanext.upload.controller import UPLOAD_ACTION
        import ckan.model as model
        import ckan.authz as authz
        is_authorized = authz.Authorizer.is_authorized('tester', UPLOAD_ACTION, model.System()) 
        assert is_authorized

    def test_03_authorization_wui(self):
        url = url_for('upload')
        res = self.app.get(url, status=[302,401])
        if res.status == 302:
            res = res.follow()
            assert 'Login' in res, res

    def test_04_index(self):
        extra_environ = {'REMOTE_USER': 'tester'}
        url = url_for('upload')
        out = self.app.get(url, extra_environ=extra_environ)
        assert 'Upload' in out, out
        assert 'action="https://commondatastorage.googleapis.com/ckan' in out, out
        assert 'key" value="' in out, out
        assert 'policy" value="' in out, out
        assert 'failure_action_redirect' in out, out
        assert 'success_action_redirect' in out, out

        url = url_for('upload', filepath='xyz.txt')
        out = self.app.get(url, extra_environ=extra_environ)
        assert 'key" value="xyz.txt"' in out, out
