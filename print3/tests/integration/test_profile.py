# -*- coding: utf-8 -*-

from chsdi.tests.integration import TestsBase


class TestProfileView(TestsBase):

    def setUp(self):
        super(TestProfileView, self).setUp()
        self.headers = {'X-SearchServer-Authorized': 'true'}

    def test_profile_json_valid(self):
        resp = self.testapp.get('/rest/services/profile.json', params={'geom': '{"type":"LineString","coordinates":[[550050,206550],[556950,204150],[561050,207950]]}'}, headers=self.headers, status=200)
        self.assertEqual(resp.content_type, 'application/json')
        self.assertEqual(resp.json[0]['dist'], 0)
        self.assertEqual(resp.json[0]['alts']['DTM25'], 1138)
        self.assertEqual(resp.json[0]['easting'], 550050)
        self.assertEqual(resp.json[0]['northing'], 206550)

    def test_profile_no_headers(self):
        self.testapp.get('/rest/services/profile.json', params={'geom': '{"type":"LineString","coordinates":[[550050,206550],[556950,204150],[561050,207950]]}'}, status=403)

    def test_profile_json_2_models(self):
        params = {'geom': '{"type":"LineString","coordinates":[[550050,206550],[556950,204150],[561050,207950]]}', 'elevation_models': 'DTM25,DTM2'}
        resp = self.testapp.get('/rest/services/profile.json', params=params, headers=self.headers, status=200)
        self.assertEqual(resp.content_type, 'application/json')
        self.assertEqual(resp.json[0]['dist'], 0)
        self.assertEqual(resp.json[0]['alts']['DTM25'], 1138)
        self.assertEqual(resp.json[0]['alts']['DTM2'], 1138.9)
        self.assertEqual(resp.json[0]['easting'], 550050)
        self.assertEqual(resp.json[0]['northing'], 206550)

    def test_profile_layers(self):
        params = {'geom': '{"type":"LineString","coordinates":[[550050,206550],[556950,204150],[561050,207950]]}', 'layers': 'DTM25,DTM2'}
        resp = self.testapp.get('/rest/services/profile.json', params=params, headers=self.headers, status=200)
        self.assertEqual(resp.content_type, 'application/json')

    def test_profile_layers_none(self):
        params = {'geom': '{"type":"LineString","coordinates":[[0,0],[0,0],[0,0]]}', 'layers': 'DTM25,DTM2'}
        resp = self.testapp.get('/rest/services/profile.json', params=params, headers=self.headers, status=200)
        self.assertEqual(resp.content_type, 'application/json')

    def test_profile_layers_none2(self):
        params = {'geom': '{"type":"LineString","coordinates":[[550050,-206550],[556950,204150],[561050,207950]]}', 'layers': 'DTM25,DTM2'}
        resp = self.testapp.get('/rest/services/profile.json', params=params, headers=self.headers, status=200)
        self.assertEqual(resp.content_type, 'application/json')

    def test_profile_json_2_models_notvalid(self):
        params = {'geom': '{"type":"LineString","coordinates":[[550050,206550],[556950,204150],[561050,207950]]}', 'elevation_models': 'DTM25,DTM222'}
        resp = self.testapp.get('/rest/services/profile.json', params=params, headers=self.headers, status=400)
        resp.mustcontain('Please provide a valid name for the elevation model DTM25, DTM2 or COMB')

    def test_profile_json_with_callback_valid(self):
        params = {'geom': '{"type":"LineString","coordinates":[[550050,206550],[556950,204150],[561050,207950]]}', 'callback': 'cb'}
        resp = self.testapp.get('/rest/services/profile.json', params=params, headers=self.headers, status=200)
        self.assertEqual(resp.content_type, 'application/javascript')
        resp.mustcontain('cb([')

    def test_profile_json_missing_geom(self):
        resp = self.testapp.get('/rest/services/profile.json', headers=self.headers, status=400)
        resp.mustcontain('Missing parameter geom')

    def test_profile_json_wrong_geom(self):
        params = {'geom': 'toto'}
        resp = self.testapp.get('/rest/services/profile.json', params=params, headers=self.headers, status=400)
        resp.mustcontain('Error loading geometry in JSON string')

    def test_profile_json_wrong_shape(self):
        params = {'geom': '{"type":"OneShape","coordinates":[[550050,206550],[556950,204150],[561050,207950]]}'}
        resp = self.testapp.get('/rest/services/profile.json', params=params, headers=self.headers, status=400)
        resp.mustcontain('Error converting JSON to Shape')

    def test_profile_json_nb_points(self):
        params = {'geom': '{"type":"LineString","coordinates":[[550050,206550],[556950,204150],[561050,207950]]}', 'nb_points': '150'}
        resp = self.testapp.get('/rest/services/profile.json', params=params, headers=self.headers, status=200)
        self.assertEqual(resp.content_type, 'application/json')

    def test_profile_json_simplify_linestring(self):
        params = {'geom': '{"type":"LineString","coordinates":[[550050,206550],[556950,204150],[561050,207950]]}', 'nb_points': '1'}
        resp = self.testapp.get('/rest/services/profile.json', params=params, headers=self.headers, status=200)
        self.assertEqual(resp.content_type, 'application/json')

    def test_profile_json_nbPoints(self):
        params = {'geom': '{"type":"LineString","coordinates":[[550050,206550],[556950,204150],[561050,207950]]}', 'nbPoints': '150'}
        resp = self.testapp.get('/rest/services/profile.json', params=params, headers=self.headers, status=200)
        self.assertEqual(resp.content_type, 'application/json')

    def test_profile_json_nb_points_wrong(self):
        params = {'geom': '{"type":"LineString","coordinates":[[550050,206550],[556950,204150],[561050,207950]]}', 'nb_points': 'toto'}
        resp = self.testapp.get('/rest/services/profile.json', params=params, headers=self.headers, status=400)
        resp.mustcontain("Please provide a numerical value for the parameter 'NbPoints'/'nb_points'")

    def test_profile_csv_valid(self):
        params = {'geom': '{"type":"LineString","coordinates":[[550050,206550],[556950,204150],[561050,207950]]}'}
        resp = self.testapp.get('/rest/services/profile.csv', params=params, headers=self.headers, status=200)
        self.assertEqual(resp.content_type, 'text/csv')

    def test_profile_cvs_wrong_geom(self):
        params = {'geom': 'toto'}
        resp = self.testapp.get('/rest/services/profile.csv', params=params, headers=self.headers, status=400)
        resp.mustcontain('Error loading geometry in JSON string')

    def test_profile_csv_wrong_shape(self):
        params = {'geom': '{"type":"OneShape","coordinates":[[550050,206550],[556950,204150],[561050,207950]]}'}
        resp = self.testapp.get('/rest/services/profile.csv', params=params, headers=self.headers, status=400)
        resp.mustcontain('Error converting JSON to Shape')

    def test_profile_json_invalid_linestring(self):
        resp = self.testapp.get('/rest/services/profile.json', params={'geom': '{"type":"LineString","coordinates":[[550050,206550]]}'}, headers=self.headers, status=400)
        resp.mustcontain('Invalid Linestring syntax')

    def test_profile_json_offset(self):
        params = {'geom': '{"type":"LineString","coordinates":[[550050,206550],[556950,204150],[561050,207950]]}', 'offset': '1'}
        resp = self.testapp.get('/rest/services/profile.json', params=params, headers=self.headers, status=200)
        self.assertTrue(resp.content_type == 'application/json')

    def test_profile_json_invalid_offset(self):
        params = {'geom': '{"type":"LineString","coordinates":[[550050,206550],[556950,204150],[561050,207950]]}', 'offset': 'asdf'}
        resp = self.testapp.get('/rest/services/profile.json', params=params, headers=self.headers, status=400)
        resp.mustcontain("Please provide a numerical value for the parameter 'offset'")
