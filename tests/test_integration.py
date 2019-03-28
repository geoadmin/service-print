import mock
import unittest
from requests import ConnectionError
from print3.main import app


class TestServicePrintIntegration(unittest.TestCase):

    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        self.patch = None

    def tearDown(self):
        if self.patch:
            self.patch.stop()

    def test_checker(self):
        resp = self.app.get('/checker')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data, b'OK')

    def test_backend_checker(self):
        def get_tomcat_backend_info_patch():
            return 'OK'

        self.patch = mock.patch(
            'print3.main.get_tomcat_backend_info',
            get_tomcat_backend_info_patch)
        self.patch.start()

        resp = self.app.get('/backend_checker')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data, b'OK')

    def test_backend_checker_down(self):
        def get_tomcat_backend_info_patch():
            raise ConnectionError

        self.patch = mock.patch(
            'print3.main.get_tomcat_backend_info',
            get_tomcat_backend_info_patch)
        self.patch.start()

        resp = self.app.get('/backend_checker')
        self.assertEqual(resp.status_code, 502)
