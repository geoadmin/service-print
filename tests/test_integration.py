import mock
import unittest
import requests
import requests_mock
from requests.exceptions import Timeout, ConnectionError, SSLError
from print3.main import  app


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
        self.assertEqual(resp.data, 'OK')

    def test_backend_checker(self):
        def get_tomcat_backend_info_patch():
            return '''{"scales":[{"name":"1:500","value":"500.0"},{"name":"1:1,000","value":"1000.0"},{"name":"1:2,500","value":"2500.0"},{"name":"1:5,000","value":"5000.0"},{"name":"1:10,000","value":"10000.0"},{"name":"1:20,000","value":"20000.0"},{"name":"1:25,000","value":"25000.0"},{"name":"1:50,000","value":"50000.0"},{"name":"1:100,000","value":"100000.0"},{"name":"1:200,000","value":"200000.0"},{"name":"1:300,000","value":"300000.0"},{"name":"1:500,000","value":"500000.0"},{"name":"1:1,000,000","value":"1000000.0"},{"name":"1:1,500,000","value":"1500000.0"},{"name":"1:2,500,000","value":"2500000.0"}],"dpis":[{"name":"150","value":"150"}],"outputFormats":[{"name":"pdf"}],"layouts":[{"name":"1 A4 landscape","map":{"width":802,"height":530},"rotation":true},{"name":"2 A4 portrait","map":{"width":550,"height":760},"rotation":true},{"name":"3 A3 landscape","map":{"width":1150,"height":777},"rotation":true},{"name":"4 A3 portrait","map":{"width":802,"height":1108},"rotation":true}],"printURL":"http://localhost:8011/service-print-main/pdf/print.pdf","createURL":"http://localhost:8011/service-print-main/pdf/create.json"}'''

        self.patch = mock.patch(
            'print3.main.get_tomcat_backend_info', get_tomcat_backend_info_patch)
        self.patch.start()

        resp = self.app.get('/backend_checker')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data, 'OK')

    def test_backend_checker_down(self):
        def get_tomcat_backend_info_patch():
            raise ConnectionError

        self.patch = mock.patch(
            'print3.main.get_tomcat_backend_info', get_tomcat_backend_info_patch)
        self.patch.start()

        resp = self.app.get('/backend_checker')
        self.assertEqual(resp.status_code, 502)
        


