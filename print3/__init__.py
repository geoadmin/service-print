# -*- coding: utf-8 -*-

from pyramid.config import Configurator
from pyramid.renderers import JSONP


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    app_version = settings.get('app_version')
    settings['app_version'] = app_version
    config = Configurator(settings=settings)

    # renderers
    config.add_renderer('jsonp', JSONP(param_name='callback', indent=None, separators=(',', ':')))

    # route definitions
    config.add_route('ogcproxy', '/ogcproxy')
    config.add_route('print_create', '/print/geoadmin3/report.pdf')
    config.add_route('print_progress', '/print/status/{id}.json')
    config.add_route('print_cancel', '/print/cancel/{id}')
    config.add_route('dev', '/dev')
    config.add_route('checker', '/checker')
    config.add_route('checker_dev', '/checker_dev')

    config.add_route('get_timestamps', '/printmulti/timestamps')
    config.add_static_view('/', 'print3:static/')

    # required to find code decorated by view_config
    config.scan(ignore=['print3.tests', 'print3.models.bod'])
    return config.make_wsgi_app()
