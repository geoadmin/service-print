# -*- coding: utf-8 -*-

from chsdi.tests.integration import TestsBase


class TestHeightView(TestsBase):

    def setUp(self):
        super(TestHeightView, self).setUp()
        self.headers = {'X-SearchServer-Authorized': 'true'}

    def test_height_valid(self):
        resp = self.testapp.get('/rest/services/height', params={'easting': '600000.1', 'northing': '200000.1'}, headers=self.headers, status=200)
        self.assertEqual(resp.content_type, 'application/json')
        self.assertEqual(resp.json['height'], '560.2')

    def test_height_none(self):
        resp = self.testapp.get('/rest/services/height', params={'easting': '600000', 'northing': '0'}, headers=self.headers, status=400)
        resp.mustcontain('Requested coordinate out of bounds')

    def test_height_nan(self):
        resp = self.testapp.get('/rest/services/height', params={'easting': 'NaN', 'northing': '200000.1'}, headers=self.headers, status=400)
        resp.mustcontain('Please provide numerical values for the parameter \'easting\'/\'lon\'')
        resp = self.testapp.get('/rest/services/height', params={'easting': '600000', 'northing': 'NaN'}, headers=self.headers, status=400)
        resp.mustcontain('Please provide numerical values for the parameter \'northing\'/\'lat\'')

    def test_height_no_header(self):
        self.testapp.get('/rest/services/height', params={'easting': '600000', 'northing': '200000'}, status=403)

    def test_height_valid_with_lonlat(self):
        resp = self.testapp.get('/rest/services/height', params={'lon': '600000.1', 'lat': '200000.1'}, headers=self.headers, status=200)
        self.assertEqual(resp.content_type, 'application/json')
        self.assertEqual(resp.json['height'], '560.2')

    def test_height_with_dtm2(self):
        resp = self.testapp.get('/rest/services/height', params={'easting': '600000.1', 'northing': '200000.1', 'layers': 'DTM2'}, headers=self.headers, status=200)
        self.assertEqual(resp.content_type, 'application/json')
        self.assertEqual(resp.json['height'], '556.5')

    def test_height_with_dtm2_elevModel(self):
        resp = self.testapp.get('/rest/services/height', params={'easting': '600000.1', 'northing': '200000.1', 'elevation_model': 'DTM2'}, headers=self.headers, status=200)
        self.assertEqual(resp.content_type, 'application/json')
        self.assertEqual(resp.json['height'], '556.5')

    def test_height_with_comb(self):
        resp = self.testapp.get('/rest/services/height', params={'easting': '600000.1', 'northing': '200000.1', 'layers': 'COMB'}, headers=self.headers, status=200)
        self.assertEqual(resp.content_type, 'application/json')
        self.assertEqual(resp.json['height'], '556.5')

    def test_height_with_comb_elevModel(self):
        resp = self.testapp.get('/rest/services/height', params={'easting': '600000.1', 'northing': '200000.1', 'elevation_model': 'COMB'}, headers=self.headers, status=200)
        self.assertEqual(resp.content_type, 'application/json')
        self.assertEqual(resp.json['height'], '556.5')

    def test_height_wrong_layer(self):
        resp = self.testapp.get('/rest/services/height', params={'easting': '600000', 'northing': '200000', 'layers': 'TOTO'}, headers=self.headers, status=400)
        resp.mustcontain("Please provide a valid name for the elevation")

    def test_height_wrong_layer_elevModel(self):
        resp = self.testapp.get('/rest/services/height', params={'easting': '600000', 'northing': '200000', 'elevation_model': 'TOTO'}, headers=self.headers, status=400)
        resp.mustcontain("Please provide a valid name for the elevation")

    def test_height_wrong_lon_value(self):
        resp = self.testapp.get('/rest/services/height', params={'lon': 'toto', 'northing': '200000'}, headers=self.headers, status=400)
        resp.mustcontain("Please provide numerical values")

    def test_height_wrong_lat_value(self):
        resp = self.testapp.get('/rest/services/height', params={'lon': '600000', 'northing': 'toto'}, headers=self.headers, status=400)
        resp.mustcontain("Please provide numerical values")

    def test_height_with_callback_valid(self):
        resp = self.testapp.get('/rest/services/height', params={'easting': '600000', 'northing': '200000', 'callback': 'cb'}, headers=self.headers, status=200)
        self.assertTrue(resp.content_type == 'application/javascript')
        resp.mustcontain('cb({')

    def test_height_miss_northing(self):
        resp = self.testapp.get('/rest/services/height', params={'easting': '600000'}, headers=self.headers, status=400)
        resp.mustcontain("Missing parameter 'norhting'/'lat'")

    def test_height_miss_easting(self):
        resp = self.testapp.get('/rest/services/height', params={'northing': '200000'}, headers=self.headers, status=400)
        resp.mustcontain("Missing parameter 'easting'/'lon'")
