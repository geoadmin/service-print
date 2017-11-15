# -*- coding: utf-8 -*-

import requests
from requests.exceptions import Timeout, ConnectionError, SSLError

from pyramid.view import view_config
from pyramid.response import Response
from pyramid.httpexceptions import HTTPBadGateway, HTTPGatewayTimeout, HTTPServiceUnavailable

req_session = requests.Session()
req_session.mount('http://', requests.adapters.HTTPAdapter(max_retries=0))


class Checker(object):

    def __init__(self, request):
        self.request = request

    @view_config(route_name='checker')
    def home(self):
        return Response(body='OK', status_int=200)

    @view_config(route_name='checker_dev')
    def dev(self):
        return Response(body='OK', status_int=200)

    @view_config(route_name='backend_checker')
    def dev(self):
        settings = self.request.registry.settings
        tomcat_port = settings.get('tomcat_port', 8010)
        tomcat_url = 'http://localhost:{}'.format(tomcat_port)
        content = ''

        try:
            r = req_session.get(tomcat_url,
                    headers={'Referer': 'service print checker'},
                    verify=False)
            content = r.content
        except (Timeout, SSLError, ConnectionError):
            return HTTPBadGateway(detail='Cannot connect to backend tomcat')

        if content == 'OK':
            return Response(body='OK', status_int=200)

        return HTTPServiceUnavailable(detail='Incomprehensible answer. tomcat is probably not ready yet.')
