# -*- coding: utf-8 -*-

import os

from pyramid.paster import get_app


class MapProxyTestsBase(object):

    def setUp(self):
        app = get_app('development.ini')
        registry = app.registry
        try:
            os.environ["http_proxy"] = registry.settings['http_proxy']
            apache_entry_path = registry.settings['apache_entry_path']
            self.mapproxy_url = "http://" + registry.settings['mapproxyhost'] + '/'
            self.host_url = "http://" + registry.settings['host'] + apache_entry_path
        except KeyError as e:
            raise e
        self.BAD_REFERER = 'http://foo.ch'
        self.GOOD_REFERER = 'http://unittest.geo.admin.ch'
        self.EPSGS = [21781, 4326, 4258, 2056, 3857]

    def tearDown(self):
        if "http_proxy" in os.environ:
            del os.environ["http_proxy"]

    def hash(self, bits=96):
        assert bits % 8 == 0
        return os.urandom(bits / 8).encode('hex')
